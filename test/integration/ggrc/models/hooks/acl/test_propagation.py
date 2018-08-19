# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test Access Control Propagation for Audit Roles like
   Auditor & Audit Captains"""

# pylint: disable=protected-access
# Disable protected access since this test suite tests internal function for
# ACL propagation.

import itertools
from collections import defaultdict
from collections import OrderedDict

import ddt
import flask
import sqlalchemy as sa
from sqlalchemy.orm.session import Session

from ggrc import app
from ggrc import db
from ggrc.models import all_models
from ggrc.models.hooks import acl
from ggrc.models.hooks.acl import propagation
from integration.ggrc import TestCase
from integration.ggrc.models import factories
from integration.ggrc_workflows.models import factories as wf_factories


class BaseTestPropagation(TestCase):
  """Base test case for all propagation scenarios."""

  def setUp(self):
    super(BaseTestPropagation, self).setUp()
    self.roles = defaultdict(dict)
    for role in all_models.AccessControlRole.query:
      self.roles[role.object_type][role.name] = role


@ddt.ddt
class TestPropagation(BaseTestPropagation):
  """TestAuditRoleProgation"""

  def setUp(self):
    super(TestPropagation, self).setUp()
    sa.event.remove(Session, "after_flush", acl.after_flush)

  def tearDown(self):
    sa.event.listen(Session, "after_flush", acl.after_flush)

  @ddt.data(
      ("source", "destination"),
      ("destination", "source"),
  )
  def test_single_acl(self, rel_order):
    """Test propagation for a single relationship with {}.

    Test propagation of program role to audit through a relationship with both
    options for source and destination.
    """
    with factories.single_commit():
      person = factories.PersonFactory()
      audit = factories.AuditFactory()
      rel_data = {
          rel_order[0]: audit,
          rel_order[1]: audit.program,
      }
      factories.RelationshipFactory(**rel_data)
      acl_entry = factories.AccessControlListFactory(
          ac_role=self.roles["Program"]["Program Editors"],
          object=audit.program,
          person=person,
      )

    self.assertEqual(all_models.AccessControlList.query.count(), 1)
    propagation._handle_acl_step([acl_entry.id])
    db.session.commit()
    self.assertEqual(all_models.AccessControlList.query.count(), 3)

  @ddt.data(0, 2, 3)
  def test_single_acl_to_multiple(self, count):
    """Test propagation of single ACL entry to multiple children."""
    with factories.single_commit():
      person = factories.PersonFactory()
      program = factories.ProgramFactory()
      for i in range(count):
        audit = factories.AuditFactory(program=program)
        factories.RelationshipFactory(
            source=program if i % 2 == 0 else audit,
            destination=program if i % 2 == 1 else audit,
        )
      acl_entry = factories.AccessControlListFactory(
          ac_role=self.roles["Program"]["Program Editors"],
          object=program,
          person=person,
      )

    self.assertEqual(all_models.AccessControlList.query.count(), 1)
    child_ids = propagation._handle_acl_step([acl_entry.id])

    self.assertEqual(
        all_models.AccessControlList.query.count(),
        # 1 original ACL entry, 2*count for objects+relationships
        1 + count * 2
    )
    self.assertEqual(
        db.session.execute(child_ids.alias("counts").count()).scalar(),
        count,
    )

  @ddt.data(1, 2, 3)
  def test_multi_acl_to_multiple(self, people_count):
    """Test multiple ACL propagation to multiple children."""
    audit_count = 3
    program_roles = ["Program Editors", "Program Readers"]
    with factories.single_commit():
      people = [factories.PersonFactory() for _ in range(people_count)]
      program = factories.ProgramFactory()
      for i in range(audit_count):
        audit = factories.AuditFactory(program=program)
        factories.RelationshipFactory(
            source=program if i % 2 == 0 else audit,
            destination=program if i % 2 == 1 else audit,
        )
      acl_ids = []
      for person in people:
        for role_name in program_roles:
          acl_ids.append(
              factories.AccessControlListFactory(
                  ac_role=self.roles["Program"][role_name],
                  object=program,
                  person=person,
              ).id,
          )

    self.assertEqual(
        all_models.AccessControlList.query.count(),
        people_count * len(program_roles)
    )
    child_ids = propagation._handle_acl_step(acl_ids)

    self.assertEqual(
        all_models.AccessControlList.query.count(),
        len(acl_ids) + len(acl_ids) * audit_count * 2
    )
    self.assertEqual(
        db.session.execute(child_ids.alias("counts").count()).scalar(),
        audit_count * len(program_roles) * people_count
    )

  @ddt.data(1, 2, 3)
  def test_partial_acl_to_multiple(self, partial_count):
    """Test propagating only a few acl entries to multiple objects."""
    audit_count = 3
    people_count = 4
    program_roles = ["Program Editors", "Program Readers"]
    with factories.single_commit():
      people = [factories.PersonFactory() for _ in range(people_count)]
      program = factories.ProgramFactory()
      for i in range(audit_count):
        audit = factories.AuditFactory(program=program)
        factories.RelationshipFactory(
            source=program if i % 2 == 0 else audit,
            destination=program if i % 2 == 1 else audit,
        )
      acl_ids = []
      for person in people:
        for role_name in program_roles:
          acl_ids.append(
              factories.AccessControlListFactory(
                  ac_role=self.roles["Program"][role_name],
                  object=program,
                  person=person,
              ).id,
          )

    self.assertEqual(
        all_models.AccessControlList.query.count(),
        people_count * len(program_roles)
    )
    propagate_acl_ids = acl_ids[:partial_count]
    child_ids = propagation._handle_acl_step(propagate_acl_ids)

    self.assertEqual(
        all_models.AccessControlList.query.count(),
        len(acl_ids) + len(propagate_acl_ids) * audit_count * 2
    )
    self.assertEqual(
        db.session.execute(child_ids.alias("counts").count()).scalar(),
        audit_count * len(propagate_acl_ids)
    )

  def test_deep_propagation(self):
    """Test nested propagation from programs to assessments.

    Test 3 people with 2 roles on programs to propagate to assessments
    """
    audit_count = 3
    people_count = 3
    program_roles = ["Program Editors", "Program Readers"]
    with factories.single_commit():
      people = [factories.PersonFactory() for _ in range(people_count)]
      for i in range(audit_count):
        audit = factories.AuditFactory()
        assessment = factories.AssessmentFactory(audit=audit)
        factories.RelationshipFactory(
            source=audit.program if i % 2 == 0 else audit,
            destination=audit.program if i % 2 == 1 else audit,
        )
        factories.RelationshipFactory(
            source=assessment if i % 2 == 0 else audit,
            destination=assessment if i % 2 == 1 else audit,
        )
        acl_ids = []

        for person in people:
          for role_name in program_roles:
            acl_ids.append(
                factories.AccessControlListFactory(
                    ac_role=self.roles["Program"][role_name],
                    object=audit.program,
                    person=person,
                ).id,
            )

    propagation._propagate(acl_ids)

    assessment_acls = all_models.AccessControlList.query.filter(
        all_models.AccessControlList.object_type ==
        all_models.Assessment.__name__
    ).all()

    self.assertEqual(
        len(assessment_acls),
        3 * 2  # 3 people each with 2 roles on a program that should be
        # propagated
    )
    for assessment_acl in assessment_acls:
      self.assertIsNotNone(assessment_acl.parent_id)

  def test_relationship_single_layer(self):
    """Test single layer propagation through relationships.

    Test propagation of a new relationship between audit and assessment. Here
    we check that propagation happens both ways on the relationship creation.
    """

    with factories.single_commit():
      person = factories.PersonFactory()
      audit = factories.AuditFactory()
      assessment1 = factories.AssessmentFactory(audit=audit)
      assessment2 = factories.AssessmentFactory(audit=audit)

      # This is excluded from propagation to test for proper filtering
      assessment3 = factories.AssessmentFactory(audit=audit)
      factories.RelationshipFactory(source=assessment3, destination=audit)

      relationship_ids = [
          factories.RelationshipFactory(
              source=assessment1,
              destination=audit,
          ).id,
          factories.RelationshipFactory(
              source=audit,
              destination=assessment2,
          ).id,
      ]

      factories.AccessControlListFactory(
          ac_role=self.roles["Audit"]["Audit Captains"],
          object=audit,
          person=person,
      )
      factories.AccessControlListFactory(
          ac_role=self.roles["Assessment"]["Assignees"],
          object=assessment1,
          person=person,
      )
      factories.AccessControlListFactory(
          ac_role=self.roles["Assessment"]["Assignees"],
          object=assessment2,
          person=person,
      )

    child_ids = propagation._handle_relationship_step(relationship_ids, [])

    self.assertEqual(
        all_models.AccessControlList.query.count(),
        3 + 2 + 2 + 4
        # 3 Initial roles
        # 2 roles for assessment 1 propagation to relationship and audit
        # 2 roles for assessment 2 propagation to relationship and audit
        # 4 for audit role propagation to two relationships and assessments
    )
    self.assertEqual(
        db.session.execute(child_ids.alias("counts").count()).scalar(),
        4,  # audit captain to both assessments and both assignees to audit
    )

  def test_propagation_conflict(self):
    """Test propagation conflicts

    When we create a new acl entry and a new relationship in the same commit
    some roles would be propagated twice and would cause unique constraint
    errors. This test checks for the most basic such scenario.
    """
    with factories.single_commit():
      person = factories.PersonFactory()
      audit = factories.AuditFactory()
      relationship = factories.RelationshipFactory(
          source=audit,
          destination=audit.program,
      )
      acl_entry = factories.AccessControlListFactory(
          ac_role=self.roles["Program"]["Program Editors"],
          object=audit.program,
          person=person,
      )

    with app.app.app_context():
      flask.g.new_acl_ids = {acl_entry.id}
      flask.g.new_relationship_ids = {relationship.id}
      flask.g.deleted_objects = set()

      propagation.propagate()

      db.session.commit()

      self.assertEqual(all_models.AccessControlList.query.count(), 3)

  def test_propagate_all(self):
    """Test clean propagation of all ACL entries."""
    with factories.single_commit():
      person = factories.PersonFactory()
      task = wf_factories.TaskGroupTaskFactory()
      audit = factories.AuditFactory()
      factories.RelationshipFactory(
          source=audit,
          destination=audit.program,
      )
      acl_ids = [
          factories.AccessControlListFactory(
              ac_role=self.roles["Program"]["Program Editors"],
              object=audit.program,
              person=person,
          ).id
      ]
      factories.AccessControlListFactory(
          ac_role=self.roles["Workflow"]["Workflow Member"],
          object=task.workflow,
          person=person,
      )

    propagation._propagate(acl_ids)
    self.assertEqual(all_models.AccessControlList.query.count(), 4)
    propagation.propagate_all()
    self.assertEqual(all_models.AccessControlList.query.count(), 8)

  def test_complex_propagation_count(self):
    """Test multiple object ACL propagation.

    This test is meant to catch invalid ACL entries for propagation that can
    not happen.
    Example for this is propagation control -> relationships -> document. In
    that propagation rule we should only propagate control acl entries to
    relationships to documents. But what can happen is; when a control has
    multiple relationships, some to objects and only one to document, all of
    those relationships would get an ACL entry even though in some cases that
    is a propagation dead end.

    Setup for this test is:

    Objects:
      control
      regulation
      objective
      program
      audit
      assessment, assessment_2

    Relationships:
      control - regulation
      control - objective
      objective - regulations
      program - control, regulation, objective, audit
      audit - assessment, assessment_2,
      audit - control-snapshot, regulation-snapshot, objective-snapshot
      control_snapshot - regulation_snapshot
      control_snapshot - objective_snapshot
      objective_snapshot - regulations_snapshot
      document - regulation, objective, control
      evidence - assessment
    """
    # pylint: disable=too-many-locals
    with factories.single_commit():
      person = factories.PersonFactory()
      control = factories.ControlFactory()
      regulation = factories.RegulationFactory()
      objective = factories.ObjectiveFactory()
      normal_objects = [control, regulation, objective]

      for obj1, obj2 in itertools.combinations(normal_objects, 2):
        factories.RelationshipFactory(source=obj1, destination=obj2)

      assessment = factories.AssessmentFactory()
      assessment_2 = factories.AssessmentFactory(audit=assessment.audit)
      factories.RelationshipFactory(
          source=assessment,
          destination=assessment.audit,
      )
      factories.RelationshipFactory(
          source=assessment_2,
          destination=assessment.audit,
      )
      factories.RelationshipFactory(
          source=assessment.audit,
          destination=assessment.audit.program,
      )
      for obj in normal_objects:
        factories.RelationshipFactory(
            source=assessment.audit.program,
            destination=obj,
        )

      snapshots = self._create_snapshots(assessment.audit, normal_objects)
      for snapshot in snapshots:
        factories.RelationshipFactory(
            source=assessment.audit,
            destination=snapshot,
        )

      for obj1, obj2 in itertools.combinations(snapshots, 2):
        factories.RelationshipFactory(source=obj1, destination=obj2)

      for obj in normal_objects:
        document = factories.DocumentFactory()
        factories.RelationshipFactory(source=obj, destination=document)

      evidence = factories.EvidenceUrlFactory()
      factories.RelationshipFactory(source=evidence, destination=assessment)

    acl_entry = factories.AccessControlListFactory(
        person=person,
        ac_role=self.roles["Control"]["Admin"],
        object=control,
    )

    propagation._propagate([acl_entry.id])

    self.assertEqual(
        all_models.AccessControlList.query.count(),
        3,  # 1 for control, 1 for relationship to document and 1 for document.
    )

    acl_entry = factories.AccessControlListFactory(
        person=person,
        ac_role=self.roles["Program"]["Program Editors"],
        object=assessment.audit.program,
    )
    propagation._propagate([acl_entry.id])

    self.assertEqual(
        all_models.AccessControlList.query.count(),
        3 + 1 + 2 + 4 + 6 + 2 + 6 + 6
        # 3 previous entries for control
        # 1 original program ACL entry
        # 2 for audit (relationship + audit propagation)
        # 4 for assessments (2 assessments and 2 relationships for them)
        # 6 for snapshots (3 snapshots with relationships)
        # 2 assessment document with relationships
        # 6 for normal objects
        # 6 for normal object documents
    )


class TestPropagationViaImport(BaseTestPropagation):
  """Test case for import propagation scenarios."""

  def test_import_propagation(self):
    """Test propagation program roles via import"""
    # pylint: disable=too-many-locals
    program_roles = ["Program Editors"]
    with factories.single_commit():
      person = factories.PersonFactory()
      program = factories.ProgramFactory()
      control = factories.ControlFactory()
      control_1 = factories.ControlFactory()
      factories.RelationshipFactory(destination=program, source=control)
      factories.RelationshipFactory(destination=program, source=control_1)
      acls = [
          factories.AccessControlListFactory(
              ac_role=self.roles["Program"][r],
              object=program,
              person=person,
          )
          for r in program_roles
      ]
    person_id = person.id
    revision = all_models.Revision.query.filter(
        all_models.Revision.resource_id == control.id,
        all_models.Revision.resource_type == control.type,
    ).first()
    with factories.single_commit():
      audit = factories.AuditFactory(program=program)
      rel = factories.RelationshipFactory(destination=audit.program,
                                          source=audit)
      snapshot = factories.SnapshotFactory(parent=audit,
                                           revision_id=revision.id,
                                           child_type=control.type,
                                           child_id=control.id)
      factories.RelationshipFactory(destination=audit, source=snapshot)
    flask.g.new_relationship_ids = [rel.id]
    flask.g.new_acl_ids = [a.id for a in acls]
    flask.g.deleted_objects = []

    propagation.propagate()
    acl_q = all_models.AccessControlList.query.filter(
        all_models.AccessControlList.person_id == person_id,
        all_models.AccessControlList.object_type == "Assessment",
    )
    acl_count_before_import = int(acl_q.count())
    response = self.import_data(
        OrderedDict([
            ("object_type", "Assessment"),
            ("Code*", ""),
            ("Audit*", audit.slug),
            ("title", "Assessment title 1"),
            ("Creators", "user@example.com"),
            ("Assignees", "user@example.com"),
            ("map:Control versions", control.slug),
        ]),
        OrderedDict([
            ("object_type", "Assessment"),
            ("Code*", ""),
            ("Audit*", audit.slug),
            ("title", "Assessment title 2"),
            ("Creators", "user@example.com"),
            ("Assignees", "user@example.com"),
            ("map:Control versions", control.slug),
        ]),
    )
    self.check_import_errors(response)
    acl_count_after_import = int(acl_q.count())
    self.assertEqual(acl_count_before_import + 2, acl_count_after_import)

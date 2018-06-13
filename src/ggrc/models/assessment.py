# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for Assessment object"""

import collections

from sqlalchemy import and_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import remote
from sqlalchemy.orm import validates
from sqlalchemy import orm

from ggrc import db
from ggrc.builder import simple_property
from ggrc.fulltext import mixin
from ggrc.models.comment import Commentable
from ggrc.models.custom_attribute_definition import CustomAttributeDefinition
from ggrc.models import issuetracker_issue, audit
from ggrc.models.mixins import with_last_comment
from ggrc.models.mixins.audit_relationship import AuditRelationship
from ggrc.models.mixins import base
from ggrc.models.mixins import BusinessObject
from ggrc.models.mixins import CustomAttributable
from ggrc.models.mixins import FinishedDate
from ggrc.models.mixins import Notifiable
from ggrc.models.mixins import TestPlanned
from ggrc.models.mixins import LastDeprecatedTimeboxed
from ggrc.models.mixins import VerifiedDate
from ggrc.models.mixins import reminderable
from ggrc.models.mixins import statusable
from ggrc.models.mixins import labeled
from ggrc.models.mixins.assignable import Assignable
from ggrc.models.mixins.autostatuschangeable import AutoStatusChangeable
from ggrc.models.mixins.issue_tracker import IssueTracked
from ggrc.models.mixins.with_action import WithAction
from ggrc.models.mixins.with_evidence import WithEvidence
from ggrc.models.mixins.with_similarity_score import WithSimilarityScore
from ggrc.models.deferred import deferred
from ggrc.models.object_person import Personable
from ggrc.models import reflection
from ggrc.models.relationship import Relatable
from ggrc.models.track_object_state import HasObjectState
from ggrc.fulltext.mixin import Indexed


class Assessment(Assignable, statusable.Statusable, AuditRelationship,
                 AutoStatusChangeable, HasObjectState, TestPlanned,
                 CustomAttributable, WithEvidence, Commentable,
                 Personable, reminderable.Reminderable, Relatable,
                 LastDeprecatedTimeboxed, WithSimilarityScore, FinishedDate,
                 VerifiedDate, Notifiable, WithAction,
                 labeled.Labeled, with_last_comment.WithLastComment,
                 IssueTracked, base.ContextRBAC, BusinessObject, Indexed,
                 db.Model):
  """Class representing Assessment.

  Assessment is an object representing an individual assessment performed on
  a specific object during an audit to ascertain whether or not
  certain conditions were met for that object.
  """

  __tablename__ = 'assessments'
  _title_uniqueness = False

  REWORK_NEEDED = u"Rework Needed"
  NOT_DONE_STATES = statusable.Statusable.NOT_DONE_STATES | {REWORK_NEEDED, }
  VALID_STATES = tuple(NOT_DONE_STATES | statusable.Statusable.DONE_STATES |
                       statusable.Statusable.INACTIVE_STATES)

  REMINDERABLE_HANDLERS = {
      "statusToPerson": {
          "handler":
              reminderable.Reminderable.handle_state_to_person_reminder,
          "data": {
              statusable.Statusable.START_STATE: "Assignees",
              "In Progress": "Assignees"
          },
          "reminders": {"assessment_assignees_reminder", }
      }
  }

  design = deferred(db.Column(db.String, nullable=False, default=""),
                    "Assessment")
  operationally = deferred(db.Column(db.String, nullable=False, default=""),
                           "Assessment")
  audit_id = deferred(
      db.Column(db.Integer, db.ForeignKey('audits.id'), nullable=False),
      'Assessment')
  assessment_type = deferred(
      db.Column(db.String, nullable=False, server_default="Control"),
      "Assessment")
  # whether to use the object test plan on snapshot mapping
  test_plan_procedure = db.Column(db.Boolean, nullable=False, default=True)

  @declared_attr
  def object_level_definitions(cls):  # pylint: disable=no-self-argument
    """Set up a backref so that we can create an object level custom
       attribute definition without the need to do a flush to get the
       assessment id.

      This is used in the relate_ca method in hooks/assessment.py.
    """
    return db.relationship(
        'CustomAttributeDefinition',
        primaryjoin=lambda: and_(
            remote(CustomAttributeDefinition.definition_id) == cls.id,
            remote(CustomAttributeDefinition.definition_type) == "assessment"),
        foreign_keys=[
            CustomAttributeDefinition.definition_id,
            CustomAttributeDefinition.definition_type
        ],
        backref='assessment_definition',
        cascade='all, delete-orphan')

  object = {}  # we add this for the sake of client side error checking

  VALID_CONCLUSIONS = frozenset([
      "Effective",
      "Ineffective",
      "Needs improvement",
      "Not Applicable"
  ])

  # REST properties
  _api_attrs = reflection.ApiAttributes(
      'design',
      'operationally',
      'audit',
      'assessment_type',
      'test_plan_procedure',
      reflection.Attribute('issue_tracker', create=False, update=False),
      reflection.Attribute('archived', create=False, update=False),
      reflection.Attribute('folder', create=False, update=False),
      reflection.Attribute('object', create=False, update=False),
  )

  _fulltext_attrs = [
      'archived',
      'design',
      'operationally',
      'folder',
  ]

  AUTO_REINDEX_RULES = [
      mixin.ReindexRule("Audit", lambda x: x.assessments, ["archived"]),
  ]

  _custom_publish = {
      'audit': audit.build_audit_stub,
  }

  @classmethod
  def _populate_query(cls, query):
    return query.options(
        orm.Load(cls).undefer_group(
            "Assessment_complete",
        ),
        orm.Load(cls).joinedload(
            "audit"
        ).undefer_group(
            "Audit_complete",
        ),
    )

  @classmethod
  def eager_query(cls):
    return cls._populate_query(super(Assessment, cls).eager_query())

  @classmethod
  def indexed_query(cls):
    return cls._populate_query(super(Assessment, cls).indexed_query())

  def log_json(self):
    out_json = super(Assessment, self).log_json()
    out_json["folder"] = self.folder
    return out_json

  _aliases = {
      "owners": None,
      "assessment_template": {
          "display_name": "Template",
          "ignore_on_update": True,
          "filter_by": "_ignore_filter",
          "type": reflection.AttributeInfo.Type.MAPPING,
      },
      "assessment_type": {
          "display_name": "Assessment Type",
          "mandatory": False,
      },
      "design": "Conclusion: Design",
      "operationally": "Conclusion: Operation",
      "archived": {
          "display_name": "Archived",
          "mandatory": False,
          "ignore_on_update": True,
          "view_only": True,
      },
      "test_plan": "Assessment Procedure",
      # Currently we decided to have 'Due Date' alias for start_date,
      # but it can be changed in future
      "start_date": "Due Date",
      "status": {
          "display_name": "State",
          "mandatory": False,
          "description": "Options are:\n{}".format('\n'.join(VALID_STATES))
      },
      "issue_tracker": {
          "display_name": "Ticket Tracker",
          "mandatory": False,
          "view_only": True,
      }
  }

  def __init__(self, *args, **kwargs):
    super(Assessment, self).__init__(*args, **kwargs)
    self._warnings = collections.defaultdict(list)

  @orm.reconstructor
  def init_on_load(self):
    self._warnings = collections.defaultdict(list)

  def add_warning(self, domain, msg):
    self._warnings[domain].append(msg)

  @simple_property
  def issue_tracker(self):
    """Returns representation of issue tracker related info as a dict."""
    issue_obj = issuetracker_issue.IssuetrackerIssue.get_issue(
        'Assessment', self.id)
    res = issue_obj.to_dict(
        include_issue=True) if issue_obj is not None else {}
    res['_warnings'] = self._warnings['issue_tracker']

    return res

  @simple_property
  def archived(self):
    """Returns a boolean whether assessment is archived or not."""
    return self.audit.archived if self.audit else False

  @simple_property
  def folder(self):
    return self.audit.folder if self.audit else ""

  def validate_conclusion(self, value):
    return value if value in self.VALID_CONCLUSIONS else ""

  @validates("status")
  def validate_status(self, key, value):
    value = super(Assessment, self).validate_status(key, value)
    # pylint: disable=unused-argument
    if self.status == value:
      return value
    if self.status == self.REWORK_NEEDED:
      valid_states = [self.DONE_STATE, self.FINAL_STATE, self.DEPRECATED]
      if value not in valid_states:
        raise ValueError("Assessment in `Rework Needed` "
                         "state can be only moved to: [{}]".format(
                             ",".join(valid_states)))
    return value

  @validates("operationally")
  def validate_opperationally(self, key, value):
    """Validate assessment operationally by validating conclusion"""
    # pylint: disable=unused-argument
    return self.validate_conclusion(value)

  @validates("design")
  def validate_design(self, key, value):
    """Validate assessment design by validating conclusion"""
    # pylint: disable=unused-argument
    return self.validate_conclusion(value)

  @validates("assessment_type")
  def validate_assessment_type(self, key, value):
    """Validate assessment type to be the same as existing model name"""
    # pylint: disable=unused-argument
    # pylint: disable=no-self-use
    from ggrc.snapshotter.rules import Types
    if value and value not in Types.all:
      raise ValueError(
          "Assessment type '{}' is not snapshotable".format(value)
      )
    return value

  @classmethod
  def _ignore_filter(cls, _):
    return None

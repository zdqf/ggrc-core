# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test acl role propagation on workflows."""

# pylint: disable=invalid-name
import datetime
from copy import deepcopy
from threading import Thread

from freezegun import freeze_time

from ggrc import db
from ggrc_workflows.models import all_models
from integration.ggrc import TestCase
from integration.ggrc.models import factories
from integration.ggrc_workflows.generator import WorkflowsGenerator


class TestWorkflowAclPropagation(TestCase):
  """Test acl role propagation on workflows."""

  def setUp(self):
    super(TestWorkflowAclPropagation, self).setUp()
    self.generator = WorkflowsGenerator()
    with factories.single_commit():
      self.people_ids = [
          factories.PersonFactory(
              name="user {}".format(i),
              email="user{}@example.com".format(i),
          ).id
          for i in range(10)
      ]

    acr = all_models.AccessControlRole
    self.acr_name_map = dict(db.session.query(
        acr.name,
        acr.id,
    ).filter(
        acr.object_type == all_models.Workflow.__name__,
    ))

    self.weekly_wf = {
        "title": "weekly thingy",
        "description": "start this many a time",
        "access_control_list": [
            {
                "ac_role_id": self.acr_name_map["Admin"],
                "person": {"type": "Person", "id": self.people_ids[i]},
            }
            for i in range(5)
        ],
        "unit": "week",
        "repeat_every": 1,
        "task_groups": [{
            "title": "weekly task group",
            "task_group_tasks": [
                {
                    "title": "weekly task {}".format(i),
                    "start_date": datetime.date(2016, 6, 10),
                    "end_date": datetime.date(2016, 6, 13),
                }
                for i in range(3)
            ]},
        ]
    }

  def test_async_role_propagation(self):
    """Test asynchronous acl propagations.

    This test just ensures that simultaneous updates to a single workflow work.
    The test checks this by first creating a workflow with first 5 out of 10
    people mapped to that workflow. Then we trigger a bunch of updates to
    workflow people while only using the last 5 people.
    In the end if the procedure does not fail or return an error on any step,
    we should see only a few of the last 5 people and none of the first 5
    people still mapped to the workflow.

    Note: This test does not check for correct setting of acl roles, but only
    that those roles that are set are correctly propagated and that propagation
    does not create any deadlocks.

    Since we have a bug with setting ACLs the result of this test will be that
    same people can have the same role on a workflow multiple times and each of
    those will have correct role propagation.
    """
    number_of_threads = 10

    def change_assignees(workflow, assignees):
      """Change workflow assignees."""
      self.generator.api.put(workflow, {
          "access_control_list": [
              {
                  "ac_role_id": self.acr_name_map["Admin"],
                  "person": {"type": "Person", "id": self.people_ids[i]},
              }
              for i in assignees
          ],
      })

    updated_wf = deepcopy(self.weekly_wf)

    with freeze_time("2016-6-10 13:00:00"):  # Friday, 6/10/2016
      _, wf = self.generator.generate_workflow(updated_wf)
      self.generator.activate_workflow(wf)

      threads = []

      for i in range(number_of_threads):
        assignees = [i % 4 + 5, i % 4 + 6]
        threads.append(Thread(target=change_assignees, args=(wf, assignees)))

      for t in threads:
        t.start()
      for t in threads:
        t.join()

      acl = all_models.AccessControlList

      workflow_role_count = acl.query.filter(
          acl.object_type == all_models.Workflow.__name__
      ).count()

      propagated_role_count = acl.query.filter(
          acl.parent_id.isnot(None)
      ).count()

      # 1 cycle
      # 1 cycle task group
      # 3 cycle tasks
      # 1 task group
      # 3 tasks
      # *2 is for all relationships that are created
      number_of_wf_objects = (1 + 1 + 3 + 1 + 3) * 2

      self.assertEqual(
          workflow_role_count * number_of_wf_objects,
          propagated_role_count
      )

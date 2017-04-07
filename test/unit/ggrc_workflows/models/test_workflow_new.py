# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module contains unittests for WorkflowNew model."""
from mock import patch, MagicMock
import unittest

from ggrc_workflows.models.workflow_new import WorkflowNew


class TestWorkflowNew(unittest.TestCase):
  """Class contains unittests for WorkflowNew model."""
  def setUp(self):
    self.day_unit = u'day'
    self.month_unit = u'month'
    self.bad_unit = u'bad_unit'

  def test_validate_unit_ok(self):
    """Tests positive cases for WorkflowNew().validate_unit() method."""
    # Note that when WorkflowNew().unit attribute value is assigned,
    # WorkflowNew().validate_unit() method runs automatically.
    workflow_none = WorkflowNew()
    workflow_none.unit = None
    self.assertIsNone(workflow_none.unit)

    workflow_day = WorkflowNew()
    workflow_day.unit = self.day_unit
    self.assertEqual(workflow_day.unit, self.day_unit)

    workflow_month = WorkflowNew()
    workflow_month.unit = self.month_unit
    self.assertEqual(workflow_month.unit, self.month_unit)

  def test_validate_unit_raises(self):
    """Tests negative case for WorkflowNew().validate_unit() method."""
    # Note that when WorkflowNew().unit attribute value is assigned,
    # WorkflowNew().validate_unit() method runs automatically.
    workflow_bad = WorkflowNew()
    with self.assertRaises(ValueError) as err:
      workflow_bad.unit = self.bad_unit
    self.assertIsNone(workflow_bad.unit)
    self.assertEqual(err.exception.message,
                     u"Invalid unit: '{}'".format(self.bad_unit))

  @patch('ggrc_workflows.models.workflow_new.exists')
  @patch('ggrc_workflows.models.workflow_new.db.session.query')
  def test_validate_parent_id_ok(self, query, _):
    """Tests positive cases for WorkflowNew().validate_parent_id() method."""
    # Note that when WorkflowNew().parent_id attribute value is assigned,
    # WorkflowNew().validate_parent_id() method runs automatically.
    query.return_value.scalar = MagicMock(return_value=True)

    workflow_none = WorkflowNew()
    workflow_none.parent_id = None
    self.assertIsNone(workflow_none.parent_id)

    workflow_256 = WorkflowNew()
    workflow_256.parent_id = 256
    self.assertEqual(workflow_256.parent_id, 256)

  @patch('ggrc_workflows.models.workflow_new.exists')
  @patch('ggrc_workflows.models.workflow_new.db.session.query')
  def test_validate_parent_id_raises(self, query, _):
    """Tests negative case for WorkflowNew().validate_parent_id() method."""
    # Note that when WorkflowNew().parent_id attribute value is assigned,
    # WorkflowNew().validate_parent_id() method runs automatically.
    query.return_value.scalar = MagicMock(return_value=False)

    bad_id = 256
    workflow_bad = WorkflowNew()
    with self.assertRaises(ValueError) as err:
      workflow_bad.parent_id = bad_id
    self.assertIsNone(workflow_bad.parent_id)
    self.assertEqual(err.exception.message,
                     u"Parent workflow with id '{}' is not "
                     u"found".format(bad_id))

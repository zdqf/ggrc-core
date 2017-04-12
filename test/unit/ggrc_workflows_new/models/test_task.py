# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module contains unittests for Task model."""
import unittest

from ddt import data, ddt, unpack
from mock import patch, MagicMock, PropertyMock

from ggrc_workflows_new.models import task

NOT_STARTED_STATUS = u'Not Started'
IN_PROGRESS_STATUS = u'In Progress'
FINISHED_STATUS = u'Finished'
TEMPLATE_STATUS = u'Template'
BAD_STATUS = u'bad_status'

INVAL_STAT_MSG = u"Task invalid status: '{}'"
TEMPL_STAT_MSG = u"Task template must have '{}' status"
NON_TEMPL_STAT_MSG = (u"Non-template task must have one of the statuses: "
                      u"'{}'")


def task_factory(status, ret_is_templ):
  """Create Task() object for Task().validate_status() testing.

  Args:
      status: Task's status to set up
      ret_is_templ: Return value for Task().is_template property.

  Returns:
      Task() object with set values and mocked 'is_template' property.
  """
  # Note that when Task().status attribute value is assigned,
  # Task().validate_status() method runs automatically.
  with patch('ggrc_workflows_new.models.task.Task.is_template',
             new_callable=PropertyMock) as is_template:
    is_template.return_value = ret_is_templ
    test_task = task.Task()
    test_task.status = status
    return test_task


@ddt
class TestTask(unittest.TestCase):
  """Class contains unittests for Task model."""
  def setUp(self):
    task.hybrid_property = MagicMock()

  @unpack
  @data((NOT_STARTED_STATUS, False), (IN_PROGRESS_STATUS, False),
        (FINISHED_STATUS, False), (TEMPLATE_STATUS, True))
  def test_validate_status_positive(self, status, ret_is_templ):
    """Tests positive cases for Task().validate_status() method."""
    self.assertEqual(task_factory(status, ret_is_templ).status, status)

  @unpack
  @data(
      (BAD_STATUS, True, INVAL_STAT_MSG.format(BAD_STATUS)),
      (BAD_STATUS, False, INVAL_STAT_MSG.format(BAD_STATUS)),
      (NOT_STARTED_STATUS, True, TEMPL_STAT_MSG.format(NOT_STARTED_STATUS)),
      (IN_PROGRESS_STATUS, True, TEMPL_STAT_MSG.format(IN_PROGRESS_STATUS)),
      (FINISHED_STATUS, True, TEMPL_STAT_MSG.format(FINISHED_STATUS)),
      (TEMPLATE_STATUS, False, NON_TEMPL_STAT_MSG.format(TEMPLATE_STATUS))
  )
  def test_validate_status_raises(self, status, ret_is_templ, err_msg):
    """Tests negative cases for Task().validate_status() method."""
    with self.assertRaises(ValueError) as err:
      self.assertIsNone(task_factory(status, ret_is_templ).status)
      self.assertEqual(err.exception.message, err_msg)

  @patch('ggrc_workflows_new.models.task.Task.workflow')
  def test_is_template(self, workflow):
    """Tests Task().is_template attribute."""
    type(workflow).is_template = PropertyMock(side_effect=(True, False))
    test_task = task.Task()
    self.assertEqual(test_task.is_template, True)
    self.assertEqual(test_task.is_template, False)

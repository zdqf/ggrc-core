# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module contains unittests for Task model."""
import unittest

from ggrc_workflows.models.task import Task


class TestTask(unittest.TestCase):
  """Class contains unittests for Task model."""
  def setUp(self):
    self.not_started_status = u'Not Started'
    self.in_progress_status = u'In Progress'
    self.finished_status = u'Finished'
    self.bad_status = u'bad_status'

  def test_validate_status_ok(self):
    """Tests positive cases for Task().validate_status() method."""
    # Note that when Task().status attribute value is assigned,
    # Task().validate_status() method runs automatically.
    valid_statuses = (None, self.not_started_status,
                      self.in_progress_status, self.finished_status)
    for status in valid_statuses:
      task = Task()
      task.status = status
      self.assertEqual(task.status, status)

  def test_validate_status_raises(self):
    """Tests negative case for Task().validate_status() method."""
    # Note that when Task().status attribute value is assigned,
    # Task().validate_status() method runs automatically.
    task_bad = Task()
    with self.assertRaises(ValueError) as err:
      task_bad.status = self.bad_status
    self.assertIsNone(task_bad.status)
    self.assertEqual(err.exception.message,
                     u"Task invalid status: '{}'".format(self.bad_status))

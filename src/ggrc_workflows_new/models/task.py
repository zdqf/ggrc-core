# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module contains 'Task' model implementation."""
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property

from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models.mixins import Described
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import Titled


class Task(Described, Slugged, Titled, db.Model):
  """Contains 'Task' model implementation."""
  __tablename__ = 'tasks'
  _title_uniqueness = False

  NOT_STARTED_STATUS = u'Not Started'
  IN_PROGRESS_STATUS = u'In Progress'
  FINISHED_STATUS = u'Finished'
  NON_TEMPLATE_STATUSES = (NOT_STARTED_STATUS, IN_PROGRESS_STATUS,
                           FINISHED_STATUS)
  TEMPLATE_STATUS = u'Template'
  VALID_STATUSES = NON_TEMPLATE_STATUSES + (TEMPLATE_STATUS, )

  contact_id = deferred(db.Column(db.Integer, db.ForeignKey('people.id'),
                                  nullable=False), 'Task')
  contact = db.relationship('Person')
  start_date = deferred(db.Column(db.Date, nullable=False), 'Task')
  end_date = deferred(db.Column(db.Date, nullable=False), 'Task')
  workflow_id = deferred(db.Column(db.Integer,
                                   db.ForeignKey('workflows_new.id'),
                                   nullable=False), 'Task')
  workflow = db.relationship('WorkflowNew', back_populates='tasks')
  status = deferred(db.Column(db.Enum(*VALID_STATUSES), nullable=False),
                    'Task')

  @hybrid_property
  def is_template(self):
    """Calculates property which shows is task template or not.

    Template tasks belong to workflow without parent. They are set up by user.
    Non-template tasks belong to workflow with parent workflow. They are
    application level generated cycle-tasks.
    """
    return self.workflow.is_template

  @validates('status')
  def validate_status(self, _, value):
    """Make sure that status value is valid."""
    if value not in self.VALID_STATUSES:
      raise ValueError(u"Task invalid status: '{}'".format(value))
    if self.is_template and value != self.TEMPLATE_STATUS:
      raise ValueError(u"Task template must have '{}' "
                       u"status".format(self.TEMPLATE_STATUS))
    if not self.is_template and value not in self.NON_TEMPLATE_STATUSES:
      raise ValueError(u"Non-template task must have one of the statuses: "
                       u"'{}'".format(', '.join(self.NON_TEMPLATE_STATUSES)))
    return value

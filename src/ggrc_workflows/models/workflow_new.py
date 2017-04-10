# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module contains new 'Workflow' model implementation."""
from sqlalchemy.orm import validates
from sqlalchemy.sql import exists
from sqlalchemy.ext.hybrid import hybrid_property

from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import Described
from ggrc.models.mixins import Titled
from ggrc_workflows.models.task import Task


class WorkflowNew(Described, Slugged, Titled, db.Model):
  """New 'Workflow' model implementation."""
  __tablename__ = 'workflows_new'
  _title_uniqueness = False

  DAY_UNIT = u'Day'
  MONTH_UNIT = u'Month'
  VALID_UNITS = (DAY_UNIT, MONTH_UNIT)

  NOT_STARTED_STATUS = u'Not Started'
  IN_PROGRESS_STATUS = u'In Progress'
  COMPLETED_STATUS = u'Completed'
  NOT_TEMPLATE_STATUS = u'Not Template'

  repeat_every = deferred(db.Column(db.Integer), 'WorkflowNew')
  unit = deferred(db.Column(db.Enum(*VALID_UNITS)), 'WorkflowNew')
  parent_id = deferred(
      db.Column(db.Integer, db.ForeignKey('{}.id'.format(__tablename__))),
      'WorkflowNew'
  )
  children = db.relationship('WorkflowNew')
  parent = db.relationship('WorkflowNew', remote_side='WorkflowNew.id')
  tasks = db.relationship('Task', back_populates='workflow')

  @hybrid_property
  def is_template(self):
    """Calculates property which shows is workflow template or not.

    Template workflow must not have parent. It is set up by user.
    Non-template workflow must have parent workflow. It is application level
    generated cycle.
    """
    return self.parent_id is None

  @hybrid_property
  def is_recurrent(self):
    """Calculates property which shows is workflow recurrent or not."""
    return self.repeat_every is not None

  @hybrid_property
  def status(self):
    """Calculates status of the workflow."""
    if not self.is_template:
      return self.NOT_TEMPLATE_STATUS
    if not self.tasks:
      return self.NOT_STARTED_STATUS
    not_finished_cycle_tasks = db.session.query(Task).filter(
        Task.workflow_id == WorkflowNew.id,
        WorkflowNew.parent_id == self.id,
        Task.status != Task.FINISHED_STATUS
    )
    if (self.is_recurrent or
            db.session.query(not_finished_cycle_tasks.exists()).scalar()):
      return self.IN_PROGRESS_STATUS
    return self.COMPLETED_STATUS

  @validates('unit')
  def validate_unit(self, _, value):
    """Make sure that unit is listed in valid units."""
    if value is not None and value not in self.VALID_UNITS:
      raise ValueError(u"Invalid unit: '{}'".format(value))
    return value

  @validates('parent_id')
  def validate_parent_id(self, _, value):  # pylint: disable=no-self-use
    """Make sure that parent object exists."""
    if value is not None and not db.session.query(
            exists().where(WorkflowNew.id == value)).scalar():
      raise ValueError(u"Parent workflow with id '{}' is "
                       u"not found".format(value))
    return value

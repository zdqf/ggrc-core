# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains new 'Workflow' model implementation."""
from sqlalchemy import orm
from sqlalchemy import sql
from sqlalchemy.ext import hybrid
from ggrc import db
from ggrc.models import context
from ggrc.models import deferred
from ggrc.models import mixins
from ggrc_workflows_new.models import task


class WorkflowNew(context.HasOwnContext, mixins.Described, mixins.Slugged,
                  mixins.Titled, db.Model):
  """New 'Workflow' model implementation."""
  __tablename__ = 'workflows_new'
  _title_uniqueness = False
  _publish_attrs = ('parent_id', 'parent', 'unit')
  DAY_UNIT = u'Day'
  MONTH_UNIT = u'Month'
  VALID_UNITS = (DAY_UNIT, MONTH_UNIT)
  NOT_STARTED_STATUS = u'Not Started'
  IN_PROGRESS_STATUS = u'In Progress'
  COMPLETED_STATUS = u'Completed'
  NOT_TEMPLATE_STATUS = u'Not Template'
  repeat_every = deferred.deferred(db.Column(db.Integer), 'WorkflowNew')
  unit = deferred.deferred(db.Column(db.Enum(*VALID_UNITS)), 'WorkflowNew')
  parent_id = deferred.deferred(
      db.Column(db.Integer, db.ForeignKey('{}.id'.format(__tablename__))),
      'WorkflowNew'
  )
  children = db.relationship('WorkflowNew')
  parent = db.relationship('WorkflowNew', remote_side='WorkflowNew.id')
  tasks = db.relationship('Task', back_populates='workflow')
  workflow_people = db.relationship('WorkflowPersonNew',
                                    back_populates='workflow')

  @hybrid.hybrid_property
  def is_template(self):
    """Calculates property which shows is workflow template or not.

    Template workflow must not have parent. It is set up by user.
    Non-template workflow must have parent workflow. It is application level
    generated cycle.
    """
    return self.parent_id is None

  @hybrid.hybrid_property
  def is_recurrent(self):
    """Calculates property which shows is workflow recurrent or not."""
    return self.repeat_every is not None

  @hybrid.hybrid_property
  def status(self):
    """Calculates status of the workflow."""
    if not self.is_template:
      return self.NOT_TEMPLATE_STATUS
    if not self.tasks:
      return self.NOT_STARTED_STATUS
    not_finished_cycle_tasks = db.session.query(task.Task).filter(
        task.Task.workflow_id == WorkflowNew.id,
        WorkflowNew.parent_id == self.id,
        task.Task.status != task.Task.FINISHED_STATUS
    )
    if (self.is_recurrent or
            db.session.query(not_finished_cycle_tasks.exists()).scalar()):
      return self.IN_PROGRESS_STATUS
    return self.COMPLETED_STATUS

  @orm.validates('unit')
  def validate_unit(self, _, value):
    """Make sure that unit is listed in valid units."""
    if value is not None and value not in self.VALID_UNITS:
      raise ValueError(u"Invalid unit: '{}'".format(value))
    return value

  @orm.validates('parent_id')
  def validate_parent_id(self, _, value):  # pylint: disable=no-self-use
    """Make sure that parent object exists.

    POST request's json should contain 'parent_id' field to run this check.
    """
    if value is not None and not db.session.query(
            sql.exists().where(WorkflowNew.id == value)).scalar():
      raise ValueError(u"Parent workflow with id '{}' is "
                       u"not found".format(value))
    return value

# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains new 'Workflow' model implementation."""
import datetime
from dateutil import relativedelta
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy import orm
from sqlalchemy import sql
from sqlalchemy.ext import declarative
from sqlalchemy.ext import hybrid
from ggrc import db
from ggrc.models import context
from ggrc.models import deferred
from ggrc.models import mixins
from ggrc.models import reflection
from ggrc_workflows_new.models import task as task_module


class WorkflowNew(context.HasOwnContext, mixins.Described, mixins.Slugged,
                  mixins.Titled, db.Model):
  """New 'Workflow' model implementation."""
  __tablename__ = 'workflows_new'
  _title_uniqueness = False
  _publish_attrs = ('parent_id', 'unit', 'labels', 'repeat_every', 'title',
                    reflection.PublishOnly('parent'),
                    reflection.PublishOnly('cycle_number'),
                    reflection.PublishOnly('latest_cycle_number'))
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
      db.Column(db.Integer,
                db.ForeignKey('{}.id'.format(__tablename__),
                              ondelete='CASCADE')), 'WorkflowNew')
  children = db.relationship('WorkflowNew', cascade='all, delete-orphan')
  parent = db.relationship('WorkflowNew', remote_side='WorkflowNew.id')
  tasks = db.relationship('Task', back_populates='workflow',
                          cascade='all, delete-orphan')
  workflow_people = db.relationship('WorkflowPersonNew',
                                    back_populates='workflow',
                                    cascade='all, delete-orphan')
  labels = db.relationship('Label', back_populates='workflow',
                           cascade='all, delete-orphan')

  @declarative.declared_attr
  def title(cls):
    return deferred.deferred(db.Column(db.String), cls.__name__)

  @hybrid.hybrid_property
  def is_template(self):
    """Calculates property which shows is workflow template or not.

    Template workflow must not have parent. It is set up by user.
    Non-template workflow must have parent workflow. It is application level
    generated cycle.
    """
    return self.parent_id is None

  @is_template.expression
  def is_template(cls):
    return cls.parent_id.is_(None)

  @hybrid.hybrid_property
  def is_recurrent(self):
    """Calculates property which shows is workflow recurrent or not."""
    return self.repeat_every is not None and self.unit is not None

  @is_recurrent.expression
  def is_recurrent(cls):
    return sa.and_(cls.repeat_every.isnot(None), cls.unit.isnot(None))

  @hybrid.hybrid_property
  def status(self):
    """Calculates status of the workflow."""
    if not self.is_template:
      return self.NOT_TEMPLATE_STATUS
    if not self.tasks:
      return self.NOT_STARTED_STATUS
    not_finished_cycle_tasks = db.session.query(task_module.Task).filter(
        task_module.Task.workflow_id == WorkflowNew.id,
        WorkflowNew.parent_id == self.id,
        task_module.Task.status != task_module.Task.FINISHED_STATUS
    )
    if (self.is_recurrent or
            db.session.query(not_finished_cycle_tasks.exists()).scalar()):
      return self.IN_PROGRESS_STATUS
    return self.COMPLETED_STATUS

  @hybrid.hybrid_property
  def cycle_number(self):
    return db.session.query(self.__class__).filter(
        self.is_template == sql.expression.false(),
        self.__class__.parent_id == self.parent_id,
        self.__class__.id <= self.id).count()

  @cycle_number.expression
  def cycle_number(cls):
    cycle = sa.orm.aliased(WorkflowNew)
    return sa.select(
        [func.count(WorkflowNew.id)]
    ).where(
        sa.and_(
            WorkflowNew.is_template == sa.sql.expression.false(),
            WorkflowNew.parent_id == cycle.parent_id,
            cycle.id <= WorkflowNew.id
        )
    ).group_by(WorkflowNew.id).label('cycle_number')

  @hybrid.hybrid_property
  def latest_cycle_number(self):
    if not isinstance(self, WorkflowNew):
      return None
    parent_id = self.id if self.is_template else self.parent_id
    return db.session.query(self.__class__).filter(
        self.__class__.parent_id == parent_id).count()

  @hybrid.hybrid_property
  def latest_cycle(self):
    if not isinstance(self, WorkflowNew):
      return None
    parent_id = self.id if self.is_template else self.parent_id
    return db.session.query(
        self.__class__,
        func.max(self.__class__.id)
    ).filter(self.__class__.parent_id == parent_id).scalar()

  @hybrid.hybrid_property
  def next_cycle_start_date(self):
    if (not self.is_template or not isinstance(self, WorkflowNew) or
            not self.is_recurrent):
      return None
    current_cycle_start_date = db.session.query(
        func.min(task_module.Task.start_date)
    ).filter(task_module.Task.workflow_id == self.id).scalar()
    delta = relativedelta.relativedelta(months=self.repeat_every) if (
        self.unit == self.MONTH_UNIT
    ) else datetime.timedelta(self.repeat_every)
    return current_cycle_start_date + delta

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

  @orm.validates('title')
  def validate_title(self, _, value):
    value = value if value is None else value.strip()
    if self.is_template:
      if value is None or len(value) == 0:
        raise ValueError(u"Workflow template cannot have empty title")
    return value

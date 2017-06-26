# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains WorkflowTemplate model implementation."""
import datetime
from dateutil import relativedelta
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy import orm
from sqlalchemy import sql
from sqlalchemy.ext import declarative
from sqlalchemy.ext import hybrid
from ggrc import db
from ggrc.models import deferred
from ggrc.models import mixins
from ggrc.models import reflection
from ggrc_workflows_new.models import task as task_module


class WorkflowTemplate(mixins.Described, mixins.Slugged,
                       mixins.Titled, db.Model):
  """WorkflowTemplate model implementation."""
  __tablename__ = 'workflow_templates'
  _title_uniqueness = False
  _publish_attrs = ('unit', 'labels', 'repeat_every', 'title',
                    reflection.PublishOnly('cycle_number'),
                    reflection.PublishOnly('latest_cycle_number'))
  DAY_UNIT = u'Day'
  MONTH_UNIT = u'Month'
  VALID_UNITS = (DAY_UNIT, MONTH_UNIT)
  repeat_every = deferred.deferred(db.Column(db.Integer), 'WorkflowNew')
  unit = deferred.deferred(db.Column(db.Enum(*VALID_UNITS)), 'WorkflowNew')


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
  def is_recurrent(self):
    """Calculates property which shows is workflow recurrent or not."""
    return self.repeat_every is not None and self.unit is not None

  @is_recurrent.expression
  def is_recurrent(cls):
    return sa.and_(cls.repeat_every.isnot(None), cls.unit.isnot(None))

  @hybrid.hybrid_property
  def cycle_number(self):
    return db.session.query(self.__class__).filter(
        self.is_template == sql.expression.false(),
        self.__class__.parent_id == self.parent_id,
        self.__class__.id <= self.id).count()

  @cycle_number.expression
  def cycle_number(cls):
    cycle = sa.orm.aliased(WorkflowTemplate)
    return sa.select(
        [func.count(WorkflowTemplate.id)]
    ).where(
        sa.and_(
          WorkflowTemplate.is_template == sa.sql.expression.false(),
          WorkflowTemplate.parent_id == cycle.parent_id,
          cycle.id <= WorkflowTemplate.id
        )
    ).group_by(WorkflowTemplate.id).label('cycle_number')

  @hybrid.hybrid_property
  def latest_cycle_number(self):
    if not isinstance(self, WorkflowTemplate):
      return None
    parent_id = self.id if self.is_template else self.parent_id
    return db.session.query(self.__class__).filter(
        self.__class__.parent_id == parent_id).count()

  @hybrid.hybrid_property
  def latest_cycle(self):
    if not isinstance(self, WorkflowTemplate):
      return None
    parent_id = self.id if self.is_template else self.parent_id
    return db.session.query(
        self.__class__,
        func.max(self.__class__.id)
    ).filter(self.__class__.parent_id == parent_id).scalar()

  @hybrid.hybrid_property
  def next_cycle_start_date(self):
    if (not self.is_template or not isinstance(self, WorkflowTemplate) or
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

  @orm.validates('title')
  def validate_title(self, _, value):
    value = value if value is None else value.strip()
    if self.is_template:
      if value is None or len(value) == 0:
        raise ValueError(u"Workflow template cannot have empty title")
    return value

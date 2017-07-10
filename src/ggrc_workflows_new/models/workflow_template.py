# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains WorkflowTemplate model implementation."""
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext import hybrid
from ggrc import db
from ggrc.models import deferred
from ggrc.models import mixins
from ggrc.models import reflection


class WorkflowTemplate(mixins.Described, mixins.Slugged, mixins.Titled,
                       db.Model):
  """WorkflowTemplate model implementation."""
  __tablename__ = 'workflow_templates'
  _title_uniqueness = False
  _publish_attrs = (reflection.PublishOnly('archived'),
                    reflection.PublishOnly('latest_cycle_number'),
                    'repeat_every', 'title', 'unit')
  DAY_UNIT = u'Day'
  WEEK_UNIT = u'Week'
  MONTH_UNIT = u'Month'
  VALID_UNITS = (DAY_UNIT, WEEK_UNIT, MONTH_UNIT)
  archived = deferred.deferred(
      db.Column(db.Boolean, nullable=False, default=False), 'WorkflowTemplate')
  latest_cycle_number = deferred.deferred(
      db.Column(db.Integer, nullable=False, default=1), 'WorkflowTemplate')
  repeat_every = deferred.deferred(db.Column(db.Integer), 'WorkflowTemplate')
  unit = deferred.deferred(db.Column(db.Enum(*VALID_UNITS)),
                           'WorkflowTemplate')

  @hybrid.hybrid_property
  def is_recurrent(self):
    """Calculates property which shows is workflow recurrent or not."""
    return self.repeat_every is not None and self.unit is not None

  @is_recurrent.expression
  def is_recurrent(cls):  # pylint: disable=no-self-argument
    return sa.and_(cls.repeat_every.isnot(None), cls.unit.isnot(None))

  @orm.validates('unit')
  def validate_unit(self, _, value):
    """Make sure that unit is listed in valid units."""
    if value is not None and value not in self.VALID_UNITS:
      raise ValueError(u"Invalid unit: '{}'".format(value))
    return value

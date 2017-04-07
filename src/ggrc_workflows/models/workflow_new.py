# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module contains new 'Workflow' model implementation."""
from sqlalchemy.orm import validates
from sqlalchemy.sql import exists

from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import Described
from ggrc.models.mixins import Titled


class WorkflowNew(Described, Slugged, Titled, db.Model):
  """New 'Workflow' model implementation."""
  __tablename__ = 'workflows_new'
  _title_uniqueness = False

  DAY_UNIT = u'day'
  MONTH_UNIT = u'month'
  VALID_UNITS = (DAY_UNIT, MONTH_UNIT)

  repeat_every = deferred(db.Column(db.Integer), 'WorkflowNew')
  unit = deferred(db.Column(db.Enum(*VALID_UNITS)), 'WorkflowNew')
  parent_id = deferred(
      db.Column(db.Integer, db.ForeignKey('{}.id'.format(__tablename__))),
      'WorkflowNew'
  )
  children = db.relationship('WorkflowNew')
  parent = db.relationship('WorkflowNew', remote_side='WorkflowNew.id')
  tasks = db.relationship('Task', back_populates='workflow')

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

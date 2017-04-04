from sqlalchemy.orm import validates

from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import Stateful
from ggrc.models.mixins import Described
from ggrc.models.mixins import Titled


class WorkflowNew(Described, Stateful, Slugged, Titled, db.Model):
  __tablename__ = 'workflows_new'
  _title_uniqueness = False

  VALID_STATES = (u"Not Started", u"In Progress", u"Completed")
  VALID_UNITS = (u'day', u'month')

  repeat_every = deferred(db.Column(db.Integer), 'WorkflowNew')
  unit = deferred(db.Column(db.Enum(*VALID_UNITS)), 'WorkflowNew')
  parent_id = deferred(db.Column(db.Integer), 'WorkflowNew')

  @validates('unit')
  def validate_unit(self, key, value):
    if value not in self.VALID_UNITS:
      raise ValueError(u"Invalid unit: '{}'".format(value))
    return value

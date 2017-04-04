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

  repeat_every = deferred(db.Column(db.Integer), 'WorkflowNew')

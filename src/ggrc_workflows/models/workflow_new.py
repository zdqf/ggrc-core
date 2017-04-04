from ggrc import db
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import Stateful
from ggrc.models.mixins import Described


class WorkflowNew(Described, Stateful, Slugged, db.Model):
  __tablename__ = 'workflows_new'

  VALID_STATES = (u"Not Started", u"In Progress", u"Completed")

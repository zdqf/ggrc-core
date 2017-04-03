from ggrc import db
from ggrc.models.mixins import Slugged


class WorkflowNew(db.Model, Slugged):
  __tablename__ = 'workflows_new'

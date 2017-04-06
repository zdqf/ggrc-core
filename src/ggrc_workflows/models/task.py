# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module contains 'Task' model implementation."""
from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models.mixins import Described
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import Stateful
from ggrc.models.mixins import Titled


class Task(Described, Slugged, Stateful, Titled, db.Model):
  """Contains 'Task' model implementation."""
  __tablename__ = 'tasks'
  _title_uniqueness = False

  contact_id = deferred(db.Column(db.Integer, db.ForeignKey('people.id'),
                                  nullable=False), 'Task')
  contact = db.relationship('Person', uselist=False,
                            foreign_keys='Task.contact_id')
  start_date = deferred(db.Column(db.Date, nullable=False), 'Task')
  end_date = deferred(db.Column(db.Date, nullable=False), 'Task')
  workflow_id = deferred(db.Column(db.Integer,
                                   db.ForeignKey('workflows_new.id'),
                                   nullable=False), 'Task')
  workflow = db.relationship('WorkflowNew', uselist=False,
                             foreign_keys='Task.workflow_id')

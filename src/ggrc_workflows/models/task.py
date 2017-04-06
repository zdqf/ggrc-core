# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module contains 'Task' model implementation."""
from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models.mixins import Described
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import Stateful
from ggrc.models.mixins import Timeboxed
from ggrc.models.mixins import Titled


class Task(Described, Slugged, Stateful, Timeboxed, Titled, db.Model):
  """Contains 'Task' model implementation."""
  __tablename__ = 'tasks'
  _title_uniqueness = False

  contact_id = deferred(db.Column(db.Integer, db.ForeignKey('people.id')),
                        'Task')
  contact = db.relationship('Person', uselist=False,
                            foreign_keys='Task.contact_id')

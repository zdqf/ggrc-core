# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains new 'WorkflowPerson' model implementation."""
from ggrc import db
from ggrc.models import deferred
from ggrc.models import mixins


class WorkflowPersonNew(mixins.Base, db.Model):
  """WorkflowPersonNew model for Workflow's people tab."""
  __tablename__ = 'workflow_people_new'
  workflow_id = deferred.deferred(
      db.Column(db.Integer, db.ForeignKey('workflows_new.id'), nullable=False),
      'WorkflowPersonNew')
  workflow = db.relationship('WorkflowNew', back_populates='workflow_people')
  person_id = deferred.deferred(
      db.Column(db.Integer, db.ForeignKey('people.id'), nullable=False),
      'WorkflowPersonNew')
  person = db.relationship('Person')

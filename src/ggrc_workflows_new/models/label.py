# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains 'Label' model implementation."""
from ggrc import db
# from ggrc.models import deferred
from ggrc.models import mixins


class Label(mixins.Base, mixins.Titled, db.Model):
  """Label model for Workflow's cycles."""
  __tablename__ = 'labels'
  _title_uniqueness = False
  # workflow_id = deferred.deferred(
  #     db.Column(db.Integer,
  #               db.ForeignKey('workflows_new.id', ondelete='CASCADE'),
  #               nullable=False), 'Label')
  # workflow = db.relationship('WorkflowNew', back_populates='labels')
  tasks = db.relationship('Task', back_populates='label')

# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains 'TaskComment' model implementation."""
from ggrc import db
from ggrc.models import deferred
from ggrc.models import mixins


class TaskComment(mixins.Base, db.Model):
  """Model for Comments on tasks."""
  __tablename__ = 'task_comments'
  _publish_attrs = ('task', 'body')
  body = deferred.deferred(db.Column(db.Text, nullable=False), 'TaskComment')
  task_id = deferred.deferred(
      db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'),
                nullable = False), 'TaskComment')
  task = db.relationship('Task', back_populates='comments')

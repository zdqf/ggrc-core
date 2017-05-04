# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains 'Task' model implementation."""
from sqlalchemy.ext import hybrid
from ggrc import db
from ggrc.models import deferred
from ggrc.models import mixins


class Task(mixins.Described, mixins.Slugged, mixins.Titled, db.Model):
  """Contains 'Task' model implementation."""
  __tablename__ = 'tasks'
  _title_uniqueness = False
  _publish_attrs = ('contact', 'start_date', 'end_date', 'workflow', 'status')
  NOT_STARTED_STATUS = u'Not Started'
  IN_PROGRESS_STATUS = u'In Progress'
  FINISHED_STATUS = u'Finished'
  NON_TEMPLATE_STATUSES = (NOT_STARTED_STATUS, IN_PROGRESS_STATUS,
                           FINISHED_STATUS)
  TEMPLATE_STATUS = u'Template'
  VALID_STATUSES = NON_TEMPLATE_STATUSES + (TEMPLATE_STATUS, )
  contact_id = deferred.deferred(db.Column(
      db.Integer, db.ForeignKey('people.id'), nullable=False), 'Task')
  contact = db.relationship('Person')
  start_date = deferred.deferred(db.Column(db.Date, nullable=False), 'Task')
  end_date = deferred.deferred(db.Column(db.Date, nullable=False), 'Task')
  workflow_id = deferred.deferred(
      db.Column(db.Integer,
                db.ForeignKey('workflows_new.id', ondelete='CASCADE'),
                nullable=False), 'Task')
  workflow = db.relationship('WorkflowNew', back_populates='tasks')
  status = deferred.deferred(db.Column(
      db.Enum(*VALID_STATUSES), nullable=False), 'Task')
  label_id = deferred.deferred(
      db.Column(db.Integer, db.ForeignKey('labels.id')), 'Task')
  label = db.relationship('Label', back_populates='tasks')
  parent_id = deferred.deferred(
    db.Column(db.Integer,
              db.ForeignKey('{}.id'.format(__tablename__),
                            ondelete='CASCADE')), 'Task')
  children = db.relationship('Task', cascade='all, delete-orphan')
  parent = db.relationship('Task', remote_side='Task.id')

  @hybrid.hybrid_property
  def is_template(self):
    """Calculates property which shows is task template or not.

    Template tasks belong to workflow without parent. They are set up by user.
    Non-template tasks belong to workflow with parent workflow. They are
    application level generated cycle-tasks.
    """
    return self.workflow.is_template

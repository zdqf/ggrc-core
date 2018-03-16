# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

""" ImportExport model."""

import json
from datetime import datetime

from sqlalchemy.dialects import mysql

from ggrc import db
from ggrc.models.mixins.base import Identifiable
from ggrc.login import get_current_user
from werkzeug.exceptions import Forbidden, NotFound


class ImportExport(Identifiable, db.Model):
  """ImportExport Model."""

  __tablename__ = 'import_exports'

  IMPORT_EXPORT_STATUSES = [
      'Not Started',
      'Analysis',
      'In Progress',
      'Blocked',
      'Analysis Failed',
      'Stopped',
      'Failed',
      'Finished',
  ]

  job_type = db.Column(db.Enum('Import', 'Export'), nullable=False)
  status = db.Column(db.Enum(*IMPORT_EXPORT_STATUSES), nullable=False,
                     default='Not Started')
  description = db.Column(db.Text)
  created_at = db.Column(db.DateTime, nullable=False)
  start_at = db.Column(db.DateTime)
  end_at = db.Column(db.DateTime)
  created_by_id = db.Column(db.Integer,
                            db.ForeignKey('people.id'), nullable=False)
  created_by = db.relationship('Person',
                               foreign_keys='ImportExport.created_by_id',
                               uselist=False)
  results = db.Column(mysql.LONGTEXT)
  title = db.Column(db.Text)
  content = db.Column(mysql.LONGTEXT)
  gdrive_metadata = db.Column('gdrive_metadata', db.Text)

  def log_json(self):
    """JSON representation"""
    res = {column.name: getattr(self, column.name)
           for column in self.__table__.columns
           if column.name not in ('content', 'gdrive_metadata')}
    if getattr(self, 'results'):
      res['results'] = json.loads(getattr(self, 'results'))
    res['created_at'] = self.created_at.isoformat()
    return res


def create_import_export_entry(**kwargs):
  """Create ImportExport entry"""
  meta = json.dumps(kwargs['gdrive_metadata']) if 'gride_metadata' in kwargs \
      else None
  ie_job = ImportExport(job_type=kwargs.get('job_type', 'Import'),
                        status=kwargs.get('status', 'Not Started'),
                        created_at=datetime.now(),
                        created_by=get_current_user(),
                        title=kwargs.get('title'),
                        content=kwargs.get('content'),
                        gdrive_metadata=meta)

  db.session.add(ie_job)
  db.session.commit()
  return ie_job


def get_jobs(job_type, ids=None):
  """Get list of jobs by type and/or ids"""
  conditions = [ImportExport.created_by == get_current_user(),
                ImportExport.job_type == job_type]
  if ids:
    conditions.append(ImportExport.id.in_(ids))
  return [ie.log_json() for ie in ImportExport.query.filter(
      *conditions)]


def get(ie_id, job_type):
  """Get import/export entry by id"""
  ie_job = ImportExport.query.get(ie_id)
  if not ie_job or ie_job.job_type != job_type:
    raise NotFound()
  if ie_job.created_by == get_current_user():
    return ie_job
  raise Forbidden()

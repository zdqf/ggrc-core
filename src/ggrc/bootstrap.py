# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import os
import sys


from ggrc import settings


def set_appengine_packages_path():
  if getattr(settings, 'APP_ENGINE', False):
    if os.path.exists(os.path.join(settings.BASE_DIR, 'packages')):
      sys.path.insert(0, os.path.join(settings.BASE_DIR, 'packages'))
    else:
      sys.path.insert(0, os.path.join(settings.BASE_DIR, 'packages.zip'))


def get_db():
  """Get modified db object."""
  from flask.ext.sqlalchemy import SQLAlchemy
  db = SQLAlchemy()

  class String(db.String):
    """Simple subclass of sqlalchemy.orm.String which provides a default
    length for `String` types to satisfy MySQL
    """

    def __init__(self, length=None, *args, **kwargs):
      # TODO: Check for MySQL and only apply when needed
      if length is None:
        length = 250
      return super(String, self).__init__(length, *args, **kwargs)
  db.String = String
  return db


set_appengine_packages_path()

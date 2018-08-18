# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


"""Entry point for all acl handlers.

This package should have the single hook that should handle all acl propagation
and deletion.
"""
import collections

import flask
import sqlalchemy as sa
from sqlalchemy.orm.session import Session

from ggrc.models import all_models
from ggrc.models.hooks.acl import propagation
from ggrc.utils import benchmark


def _add_or_update(name, value):
  """Add or update flask.g attribute."""
  if hasattr(flask.g, name):
    getattr(flask.g, name).update(value)
  else:
    setattr(flask.g, name, value)


def add_relationships(relationship_ids):
  """Add extra relationships to propagation queue.

  This function is needed to allow propagation of manually created
  relationships from raw SQL statements. The most common examples for this are
  snapshot relationships and automappings.

  Args:
    relationship_ids: set of ids that might have to propagate permissions.
  """
  _add_or_update("new_acl_ids", set())
  _add_or_update("new_relationship_ids", relationship_ids)
  _add_or_update("deleted_objects", set())


def _get_propagation_entries(session):
  """Get object ids for objects that affect propagation.

  Args:
    session: db session with all objects

  Returns:
    lists of ids of new ACL, relationship, and delete objects
  """
  propagated_models = (all_models.AccessControlList, all_models.Relationship)
  objs = collections.defaultdict(set)
  for obj in session.new:
    if not isinstance(obj, propagated_models):
      continue
    if obj.id is None:
      # This can happen if we call flush with a list of objects and only those
      # get flushed and the rest remain as None. All the none objects are still
      # inserted at the last full flush before the session gets committed.
      continue
    objs[obj.__class__].add(obj.id)

  deleted = {(obj.type, obj.id) for obj in session.deleted}

  return (objs[all_models.AccessControlList],
          objs[all_models.Relationship],
          deleted)


def after_flush(session, _):
  """Handle all ACL hooks after after flush."""
  with benchmark("handle ACL hooks after flush"):
    if not flask.has_app_context():
      return

    acl_ids, relationship_ids, deleted = _get_propagation_entries(session)

    _add_or_update("new_acl_ids", acl_ids)
    _add_or_update("new_relationship_ids", relationship_ids)
    _add_or_update("deleted_objects", deleted)


def after_commit():
  """ACL propagation after commit action."""
  with benchmark("General acl propagation"):
    propagation.propagate()


def init_hook():
  """Initialize Relationship-related hooks."""
  sa.event.listen(Session, "after_flush", after_flush)

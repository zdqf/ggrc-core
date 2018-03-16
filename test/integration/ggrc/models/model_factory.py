# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Factories for ggrc models.

These are factories for generating regular ggrc models. The factories create a
model and log a post event with the model revision. These do not however
trigger signals. For tests that rely on proper signals being triggered, we must
use the object generator in the ggrc.generator module.
"""

# pylint: disable=too-few-public-methods,missing-docstring,old-style-class
# pylint: disable=no-init

import factory

from ggrc import db
from ggrc import models
from ggrc.login import noop
from ggrc.fulltext import get_indexer


class ModelFactory(factory.Factory, object):

  @classmethod
  def _create(cls, target_class, *args, **kwargs):
    instance = target_class(*args, **kwargs)
    db.session.add(instance)
    if isinstance(instance, models.CustomAttributeValue):
      cls._log_event(instance.attributable)
    if hasattr(instance, "log_json"):
      cls._log_event(instance)
    if getattr(db.session, "single_commit", True):
      db.session.commit()
    return instance

  @classmethod
  def _log_event(cls, instance, action="POST"):
    if not hasattr(instance, 'context'):
      return
    indexer = get_indexer()
    db.session.flush()
    user = cls._get_user()
    revision = models.Revision(
        instance, user.id, 'created', instance.log_json())
    event = models.Event(
        modified_by=user,
        action=action,
        resource_id=instance.id,
        resource_type=instance.type,
        context=instance.context,
        revisions=[revision],
    )
    db.session.add(revision)
    db.session.add(event)
    indexer.update_record(indexer.fts_record_for(instance), commit=False)

  @staticmethod
  def _get_user():
    user = models.Person.query.first()
    if not user:
      user = models.Person(
          name=noop.default_user_name,
          email=noop.default_user_email,
      )
      db.session.add(user)
      db.session.flush()
    return user

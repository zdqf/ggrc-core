# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from sqlalchemy import and_

from ggrc import db
from ggrc.extensions import get_extension_modules
from ggrc.models import Audit
from ggrc.models.relationship import Relationship


class RelationshipHelper(object):

  @classmethod
  def program_audit(cls, object_type, related_type, related_ids=[]):
    if {object_type, related_type} != {"Program", "Audit"} or not related_ids:
      return None

    if object_type == "Program":
      return db.session.query(Audit.program_id).filter(
          Audit.id.in_(related_ids))
    else:
      return db.session.query(Audit.id).filter(
          Audit.program_id.in_(related_ids))

  @classmethod
  def get_special_mappings(cls, object_type, related_type, related_ids):
    return [
        cls.program_audit(object_type, related_type, related_ids)
    ]

  @classmethod
  def get_extension_mappings(cls, object_type, related_type, related_ids):
    queries = []
    for extension in get_extension_modules():
      get_ids = getattr(extension, "contributed_get_ids_related_to", None)
      if callable(get_ids):
        queries.append(get_ids(object_type, related_type, related_ids))

    return queries

  @classmethod
  def _array_union(cls, queries):
    """ Union of all valid queries in array """
    clean_queries = [q for q in queries if q is not None]
    if len(clean_queries) == 0:
      return None

    query = clean_queries.pop()
    for q in clean_queries:
      query = query.union(q)
    return query

  @classmethod
  def get_ids_related_to(cls, object_type, related_type, related_ids=[]):
    """ get ids of objects

    Get a list of all ids for object with object_type, that are related to any
    of the objects with type related_type and id in related_ids
    """

    if isinstance(related_ids, (int, long)):
      related_ids = [related_ids]

    destination_ids = db.session.query(Relationship.destination_id).filter(
        and_(
            Relationship.destination_type == object_type,
            Relationship.source_type == related_type,
            Relationship.source_id.in_(related_ids),
        )
    )
    source_ids = db.session.query(Relationship.source_id).filter(
        and_(
            Relationship.source_type == object_type,
            Relationship.destination_type == related_type,
            Relationship.destination_id.in_(related_ids),
        )
    )

    queries = [destination_ids, source_ids]
    queries.extend(cls.get_extension_mappings(
        object_type, related_type, related_ids))
    queries.extend(cls.get_special_mappings(
        object_type, related_type, related_ids))

    return cls._array_union(queries)

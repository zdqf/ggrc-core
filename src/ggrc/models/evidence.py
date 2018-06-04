# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module containing Evidence model."""

from sqlalchemy import orm

from ggrc import db
from ggrc import login
from ggrc.access_control.roleable import Roleable
from ggrc.builder import simple_property
from ggrc.fulltext import mixin
from ggrc.models.deferred import deferred
from ggrc.models import comment
from ggrc.models import exceptions
from ggrc.models import mixins
from ggrc.models import reflection
from ggrc.models.mixins import before_flush_handleable as bfh
from ggrc.models.mixins.statusable import Statusable
from ggrc.models.mixins.with_auto_deprecation import WithAutoDeprecation
from ggrc.models.relationship import Relatable
from ggrc.utils import referenced_objects


class Evidence(Roleable, Relatable, mixins.Titled,
               bfh.BeforeFlushHandleable, Statusable,
               mixins.WithLastDeprecatedDate, comment.Commentable,
               WithAutoDeprecation, mixin.Indexed, mixins.Slugged, db.Model):
  """Evidence (Audit-scope URLs, FILE's) model."""
  __tablename__ = "evidence"

  _title_uniqueness = False

  URL = "URL"
  FILE = "FILE"
  VALID_EVIDENCE_KINDS = [URL, FILE]

  START_STATE = 'Active'
  DEPRECATED = 'Deprecated'

  VALID_STATES = (START_STATE, DEPRECATED, )

  kind = deferred(db.Column(db.Enum(*VALID_EVIDENCE_KINDS),
                            default=URL,
                            nullable=False),
                  "Evidence")
  source_gdrive_id = deferred(db.Column(db.String, nullable=False,
                                        default=u""),
                              "Evidence")
  gdrive_id = deferred(db.Column(db.String, nullable=False, default=u""),
                       "Evidence")

  link = deferred(db.Column(db.String), "Evidence")

  description = deferred(db.Column(db.Text, nullable=False, default=u""),
                         "Evidence")

  # Override from Commentable mixin (can be removed after GGRC-5192)
  send_by_default = db.Column(db.Boolean, nullable=False, default=True)

  _api_attrs = reflection.ApiAttributes(
      "title",
      reflection.Attribute("link", update=False),
      reflection.Attribute("source_gdrive_id", update=False),
      "description",
      "status",
      reflection.Attribute("kind", update=False),
      reflection.Attribute("parent_obj", read=False, update=False),
      reflection.Attribute('archived', create=False, update=False),
      reflection.Attribute('is_uploaded', read=False, update=False),
  )

  _fulltext_attrs = [
      "title",
      "link",
      "description",
      "kind",
      "status",
      "archived"
  ]

  AUTO_REINDEX_RULES = [
      mixin.ReindexRule("Audit", lambda x: x.assessments, ["archived"]),
  ]

  _sanitize_html = [
      "title",
      "description",
  ]

  _aliases = {
      "title": "Title",
      "link": "Attachment",
      "description": "description",
      "kind": "type",
      "archived": {
          "display_name": "Archived",
          "mandatory": False
      },
  }

  _allowed_parents = {'Assessment', 'Audit'}
  FILE_NAME_SEPARATOR = '_ggrc'

  @orm.validates("kind")
  def validate_kind(self, key, kind):
    """Returns correct option, otherwise rises an error"""
    if kind is None:
      kind = self.URL
    if kind not in self.VALID_EVIDENCE_KINDS:
      raise exceptions.ValidationError(
          "Invalid value for attribute {attr}. "
          "Expected options are `{url}`, `{file}`".
          format(
              attr=key,
              url=self.URL,
              file=self.FILE
          )
      )
    return kind

  @classmethod
  def indexed_query(cls):
    return super(Evidence, cls).indexed_query().options(
        orm.Load(cls).undefer_group(
            "Evidence_complete",
        ),
    )

  @simple_property
  def archived(self):
    """Returns a boolean whether parent is archived or not."""
    parent_candidates = self.related_objects(_types=Evidence._allowed_parents)
    if parent_candidates:
      parent = parent_candidates.pop()
      return parent.archived
    return False

  def log_json(self):
    tmp = super(Evidence, self).log_json()
    tmp['type'] = 'Evidence'
    return tmp

  @simple_property
  def is_uploaded(self):
    """This flag is used to know if file uploaded from a local user folder.

    In that case we need just rename file, not copy.
    """
    return self._is_uploaded if hasattr(self, '_is_uploaded') else False

  @is_uploaded.setter
  def is_uploaded(self, value):
    # pylint: disable=attribute-defined-outside-init
    self._is_uploaded = value

  @simple_property
  def parent_obj(self):
    return self._parent_obj

  @parent_obj.setter
  def parent_obj(self, value):
    # pylint: disable=attribute-defined-outside-init
    self._parent_obj = value

  def _get_parent_obj(self):
    """Get parent object specified"""
    if 'id' not in self._parent_obj:
      raise exceptions.ValidationError('"id" is mandatory for parent_obj')
    if 'type' not in self._parent_obj:
      raise exceptions.ValidationError(
          '"type" is mandatory for parent_obj')
    if self._parent_obj['type'] not in self._allowed_parents:
      raise exceptions.ValidationError(
          'Allowed types are: {}.'.format(', '.join(self._allowed_parents)))

    parent_type = self._parent_obj['type']
    parent_id = self._parent_obj['id']
    obj = referenced_objects.get(parent_type, parent_id)

    if not obj:
      raise ValueError(
          'Parent object not found: {type} {id}'.format(type=parent_type,
                                                        id=parent_id))
    return obj

  @staticmethod
  def _build_file_name_postfix(parent_obj):
    """Build postfix for given parent object"""
    postfix_parts = [Evidence.FILE_NAME_SEPARATOR, parent_obj.slug]

    related_snapshots = parent_obj.related_objects(_types=['Snapshot'])
    related_snapshots = sorted(related_snapshots, key=lambda it: it.id)

    slugs = (sn.revision.content['slug'] for sn in related_snapshots if
             sn.child_type == parent_obj.assessment_type)

    postfix_parts.extend(slugs)
    postfix_sting = '_'.join(postfix_parts).lower()

    return postfix_sting

  def _build_relationship(self, parent_obj):
    """Build relationship between evidence and parent object"""
    from ggrc.models import all_models
    from ggrc.models.mixins.autostatuschangeable import AutoStatusChangeable
    rel = all_models.Relationship(
        source=parent_obj,
        destination=self
    )
    db.session.add(rel)
    if isinstance(parent_obj, AutoStatusChangeable):
      parent_obj.move_to_in_progress()

  def _update_fields(self, response):
    """Update fields of evidence with values of the copied file"""
    self.gdrive_id = response['id']
    self.link = response['webViewLink']
    self.title = response['name']
    self.kind = Evidence.FILE

  @staticmethod
  def _get_folder(parent):
    return parent.folder if hasattr(parent, 'folder') else ''

  def _map_parent(self):
    """Maps evidence to parent object

    If Document.FILE and source_gdrive_id => copy file
    """
    if self.is_with_parent_obj():
      parent = self._get_parent_obj()
      if self.kind == Evidence.FILE and self.source_gdrive_id:
        self.exec_gdrive_file_copy_flow(parent)
      self._build_relationship(parent)
      self._parent_obj = None

  def exec_gdrive_file_copy_flow(self, parent):
    """Execute google gdrive file copy flow

    Build file name, destination folder and copy file to that folder.
    After coping fills evidence object fields with new gdrive URL
    """
    postfix = self._build_file_name_postfix(parent)
    folder_id = self._get_folder(parent)
    file_id = self.source_gdrive_id
    from ggrc.gdrive.file_actions import process_gdrive_file
    response = process_gdrive_file(file_id, folder_id, postfix,
                                   separator=Evidence.FILE_NAME_SEPARATOR,
                                   is_uploaded=self.is_uploaded)
    self._update_fields(response)

  def is_with_parent_obj(self):
    return bool(hasattr(self, '_parent_obj') and self._parent_obj)

  def add_admin_role(self):
    """Add current user as Evidence admin"""
    from ggrc.models import all_models
    admin_role = db.session.query(all_models.AccessControlRole).filter_by(
        name="Admin", object_type=self.type).one()
    self.extend_access_control_list([{
        "ac_role": admin_role,
        "person": login.get_current_user()
    }])

  def handle_before_flush(self):
    """Handler that called  before SQLAlchemy flush event"""
    self._map_parent()

# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Handlers evidence entries."""

from logging import getLogger

from ggrc import models
from ggrc.converters import errors
from ggrc.converters.handlers import handlers
from ggrc.login import get_current_user_id


# pylint: disable=invalid-name
logger = getLogger(__name__)


class EvidenceUrlHandler(handlers.ColumnHandler):
  """Handler for Evidence URL field on evidence imports."""

  KIND = models.Evidence.URL

  @staticmethod
  def _parse_line(line):
    """Parse a single line and return link and title.

    Args:
      line: string containing a single line from a cell.

    Returns:
      tuple containing a link and a title.
    """
    link = title = line.strip()
    return link, title

  def _get_old_map(self):
    return {d.link: d for d in self.row_converter.obj.evidences_url}

  def get_value(self):
    """Generate a new line separated string for all document links.

    Returns:
      string containing all URLs
    """
    return "\n".join(doc.link for doc in self.row_converter.obj.evidences_url)

  def build_evidence(self, link, title, user_id):
    """Build evidence object"""
    evidence = models.Evidence(
        link=link,
        title=title,
        modified_by_id=user_id,
        context=self.row_converter.obj.context,
        kind=self.KIND,
    )
    evidence.add_admin_role()
    return evidence

  def parse_item(self):
    """Parse evidence link lines.

    Returns:
      list of evidences for all URLs and evidences.
    """
    new_links = set()
    duplicate_new_links = set()

    evidences = []
    user_id = get_current_user_id()

    for line in self.raw_value.splitlines():
      link, title = self._parse_line(line)
      if not (link and title):
        continue

      if link in new_links:
        duplicate_new_links.add(link)
      else:
        new_links.add(link)
        evidences.append(self.build_evidence(link, title, user_id))

    if duplicate_new_links:
      # NOTE: We rely on the fact that links in duplicate_new_links are all
      # instances of unicode (if that assumption breaks, unicode encode/decode
      # errors can occur for non-ascii link values)
      self.add_warning(errors.DUPLICATE_IN_MULTI_VALUE,
                       column_name=self.display_name,
                       duplicates=u", ".join(sorted(duplicate_new_links)))

    return evidences

  def set_obj_attr(self):
    self.value = self.parse_item()

  def set_value(self):
    """This should be ignored with second class attributes."""

  def insert_object(self):
    """Update document URL values

    This function adds missing URLs and remove existing ones from Documents.
    The existing URLs with new titles just change the title.
    """
    if self.row_converter.ignore:
      return
    new_link_map = {d.link: d for d in self.value}
    old_link_map = self._get_old_map()

    for new_link, new_evid in new_link_map.iteritems():
      if new_link in old_link_map:
        old_link_map[new_link].title = new_evid.title
      else:
        models.Relationship(source=self.row_converter.obj,
                            destination=new_evid)

    for old_link, old_doc in old_link_map.iteritems():
      if old_link in new_link_map:
        continue
      if old_doc.related_destinations:
        old_doc.related_destinations.pop()
      elif old_doc.related_sources:
        old_doc.related_sources.pop()
      else:
        logger.warning("Invalid relationship state for document URLs.")


class EvidenceFileHandler(EvidenceUrlHandler):
  """Handler for evidence of type file on evidence imports."""

  def set_obj_attr(self):
    """Is not allowed to import evidence of type File

    if file already mapped to parent we ignore it and not show warning
    """
    if self.raw_value:
      parent = self.row_converter.obj
      existing_evid_file_links = {evid.link for evid in parent.evidences_file}
      for line in self.raw_value.splitlines():
        link, _ = self._parse_line(line)
        if link not in existing_evid_file_links:
          self.add_warning(errors.DISALLOW_EVIDENCE_FILE)

  def insert_object(self):
    """Import not allowed"""
    pass

  @staticmethod
  def _parse_line(line):
    """Parse a single line and return link and title.

    Args:
      line: string containing a single line from a cell.

    Returns:
      tuple containing a link and a title.
    """
    parts = line.strip().split()
    return parts[0], parts[0] if len(parts) == 1 else " ".join(parts[1:])

  def get_value(self):
    """Generate a new line separated string for all document links.

    Returns:
      string containing all evidence URLs and titles.
    """
    return u"\n".join(u"{} {}".format(d.link, d.title) for d in
                      self.row_converter.obj.evidences_file)

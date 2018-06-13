# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Import GGRC model hooks."""


def init_hooks():
  """Initialize all hooks."""

  # Need to import hooks here to avoid cycle import of modules
  from ggrc.models.hooks import common
  from ggrc.models.hooks import assessment
  from ggrc.models.hooks import audit
  from ggrc.models.hooks import comment
  from ggrc.models.hooks import custom_attribute_definition
  from ggrc.models.hooks import issue
  from ggrc.models.hooks import issue_tracker
  from ggrc.models.hooks import relationship
  from ggrc.models.hooks import acl
  from ggrc.models.hooks import proposal

  all_hooks = [
      assessment,
      audit,
      comment,
      issue,
      relationship,
      custom_attribute_definition,
      acl,
      common,

      # Keep IssueTracker at the end of list to make sure that all other hooks
      # are already executed and all data is final.
      issue_tracker,
      proposal,
  ]

  for hook in all_hooks:
    hook.init_hook()

/*
 * Copyright (C) 2017 Google Inc.
 * Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function ($, CMS, GGRC) {
  var Cross = GGRC.MapperHelpers.Cross;

  // Add mappings for basic workflow objects
  var mappings = {
    Workflow: {
      current_all_tasks: Cross(
        'current_task_groups', 'cycle_task_group_tasks'
      )
    }
  };

  new GGRC.Mappings('ggrc_workflows', mappings);
})(this.can.$, this.CMS, this.GGRC);

/*
 * Copyright (C) 2017 Google Inc.
 * Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function ($, CMS, GGRC) {
  var Direct = GGRC.MapperHelpers.Direct;

  // Add mappings for basic workflow objects
  var mappings = {
    WorkflowTemplate: {
      _canonical: {
        context: 'Context'
      },
      context: Direct('Context', 'related_object', 'context')
    }
  };
  new GGRC.Mappings('ggrc_workflows', mappings);
})(this.can.$, this.CMS, this.GGRC);

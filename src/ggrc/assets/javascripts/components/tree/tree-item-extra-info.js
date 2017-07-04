/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var template = can.view(GGRC.mustache_path +
    '/components/tree/tree-item-extra-info.mustache');

  var viewModel = can.Map.extend({
    define: {
      isSubTreeItem: {
        type: 'htmlbool',
        value: false
      },
      isActive: {
        type: 'boolean',
        get: function () {
          return this.attr('drawStatuses') ||
            this.attr('isDirective') ||
            this.attr('isCycleTasks') ||
            this.attr('isSection');
        }
      },
      isDirective: {
        type: 'boolean',
        get: function () {
          return this.attr('instance') instanceof CMS.Models.Directive;
        }
      },
      isSection: {
        type: 'boolean',
        get: function () {
          return this.attr('instance') instanceof CMS.Models.Section;
        }
      },
      isTask: {
        type: 'boolean',
        get: function () {
          // return false until CMS.Models.Task is introduced
          return false;
        }
      },
      isLoading: {
        type: 'boolean',
        value: false
      },
      readyStatus: {
        type: 'boolean',
        value: false
      },
      raisePopover: {
        type: 'boolean',
        value: false,
        get: function () {
          return this.attr('hovered') || this.attr('readyStatus');
        }
      },
      disablePopover: {
        type: 'boolean',
        get: function () {
          return this.attr('instance') instanceof CMS.Models.Cycle;
        }
      },
      drawStatuses: {
        type: 'boolean',
        get: function () {
          return !!this.attr('instance.workflow_state');
        }
      },
      isShowOverdue: {
        type: 'boolean',
        get: function () {
          return this.attr('isTask');
        }
      },
      isOverdue: {
        type: 'boolean',
        get: function () {
          var isWorkflowOverdue =
            this.attr('drawStatuses') &&
            this.attr('instance.workflow_state') === 'Overdue';

          var isCycleTasksOverdue =
            this.attr('isCycleTasks') &&
            this.attr('instance.isOverdue');

          return isWorkflowOverdue || isCycleTasksOverdue;
        }
      },
      cssClasses: {
        type: 'string',
        get: function () {
          var classes = [];

          if (this.attr('isOverdue')) {
            classes.push('state-overdue');
          }

          if (this.attr('spin')) {
            classes.push('fa-spinner');
            classes.push('fa-spin');
          } else if (this.attr('active')) {
            classes.push('active');
            classes.push('fa-info-circle');
          } else {
            classes.push('fa-info-circle');
          }

          return classes.join(' ');
        }
      }
    },
    onEnter: function () {
      this.attr('active', true);
      if (!this.attr('triggered')) {
        this.attr('triggered', true);
      }
    },
    onLeave: function () {
      this.attr('active', false);
    },
    addContent: function (dataPromise) {
      var dfds = this.attr('contentPromises');
      var dfdReady = this.attr('dfdReady');

      if (dfdReady.state() === 'pending') {
        this.attr('spin', true);
        dfds.push(dataPromise);
        dfdReady = $.when.apply($, dfds).then(function () {
          this.attr('spin', false);
        }.bind(this));

        this.attr('dfdReady', dfdReady);
      }
    },
    contentPromises: [],
    dfdReady: can.Deferred(),
    classes: [],
    instance: null
  });

  GGRC.Components('treeItemExtraInfo', {
    tag: 'tree-item-extra-info',
    template: template,
    viewModel: viewModel
  });
})(window.can, window.GGRC);

/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can) {
  can.Model.Cacheable('CMS.Models.WorkflowTemplate', {
    root_object: 'workflow_template',
    root_collection: 'workflow_templates',
    category: 'workflow',
    mixins: ['ca_update', 'timeboxed'],
    findAll: 'GET /api/workflow_templates',
    findOne: 'GET /api/workflow_templates/{id}',
    create: 'POST /api/workflow_templates',
    update: 'PUT /api/workflow_templates/{id}',
    destroy: 'DELETE /api/workflow_templates/{id}',
    title_singular: 'Workflow',
    is_custom_attributable: true,

    defaults: {
      frequency_options: [
        {title: 'One time', value: 'one_time'},
        {title: 'Weekly', value: 'weekly'},
        {title: 'Monthly', value: 'monthly'}
      ],
      frequency: 'one_time' // default value
    },

    attributes: {
      people: 'CMS.Models.Person.stubs',
      workflow_people: 'CMS.Models.WorkflowPerson.stubs',
      modified_by: 'CMS.Models.Person.stub',
      context: 'CMS.Models.Context.stub',
      custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs',
      default_lhn_filters: {
        WorkflowTemplate: {}
      }
    },
    obj_nav_options: {
      show_all_tabs: true
    },
    tree_view_options: {
      attr_view: GGRC.mustache_path + '/workflows/tree-item-attr.mustache',
      attr_list: [
        {attr_title: 'Title', attr_name: 'title'},
        {attr_title: 'Manager', attr_name: 'owner', attr_sort_field: ''},
        {attr_title: 'Code', attr_name: 'slug'},
        {attr_title: 'State', attr_name: 'status'},
        {attr_title: 'Frequency', attr_name: 'frequency'},
        {attr_title: 'Last Updated', attr_name: 'updated_at'}
      ]
    },

    init: function () {
      if (this._super) {
        this._super.apply(this, arguments);
      }
      this.validateNonBlank('title');
      this.bind('destroyed', function (ev, inst) {
      });
    }
  }, {
    save: function () {
      var redirectLink;
      var dfd;

      dfd = this._super.apply(this, arguments);
      dfd.then(function (instance) {
        redirectLink = instance.viewLink;
        instance.attr('_redirect', redirectLink);
      });
      return dfd;
    },
    // Check if task groups are slated to start
    //   in the current week/month/quarter/year
    is_mid_frequency: function () {
      var dfd = new $.Deferred();
      var self = this;

      function _afterOrSame(d1, d2) {
        return d1.isAfter(d2, 'day') || d1.isSame(d2, 'day');
      }
      function _beforeOrSame(d1, d2) {
        return d1.isBefore(d2, 'day') || d1.isSame(d2, 'day');
      }
      function checkAllTasks(tasks) {
        tasks.each(function (task) {
          var start;
          var end;
          var current = moment();
          task = task.reify();
          switch (self.frequency) {
            case 'weekly':
              start = moment().isoWeekday(task.relative_start_day);
              end = moment().isoWeekday(task.relative_end_day);
              if (_afterOrSame(start, end)) {
                end.add(1, 'w');
              }
              break;
            case 'monthly':
              start = moment().date(task.relative_start_day);
              end = moment().date(task.relative_end_day);
              if (_afterOrSame(start, end)) {
                end.add(1, 'M');
              }
              break;
            default:
              dfd.resolve(false);
          }
          if (_afterOrSame(current, start) && _beforeOrSame(current, end)) {
            dfd.resolve(true);
          }
        });
        dfd.resolve(false);
      }

      if (!this.frequency_duration || this.frequency === 'one_time') {
        return dfd.resolve(false);
      }

      // Check each task in the workflow:
      this.refresh_all('task_group_tasks').then(function (taskGroupTasks) {
        var tasks = new can.List();
        taskGroupTasks.each(function (task) {
          tasks.push(task.reify());
        });
        checkAllTasks(tasks);
      });
      return dfd;
    },

    // Get duration from frequency or false for one_time or continuous wfs.
    frequency_duration: function () {
      switch (this.frequency) {
        case 'weekly': return 'week';
        case 'monthly': return 'month';
        default: return false;
      }
    }
  });
})(window.can);

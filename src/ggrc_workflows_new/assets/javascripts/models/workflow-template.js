/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, _) {
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
    }
  });
})(window.can, window._);

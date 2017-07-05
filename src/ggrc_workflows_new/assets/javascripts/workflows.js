/*
 * Copyright (C) 2017 Google Inc.
 * Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC) {
  var workflowExtension = {
    name: 'workflows'
  };
  GGRC.register_hook(
        'Dashboard.Widgets.New', GGRC.mustache_path + '/dashboard/widgets');

  workflowExtension.object_type_decision_tree = function () {
    return {
      workflow_template: CMS.Models.WorkflowTemplate
    };
  };

  workflowExtension.init_widgets_for_workflow_page = function () {
    var newWidgetDescriptors = {};
    var newDefaultWidgets = [
      'info', 'person', 'task_group', 'current', 'history'
    ];

    can.each(
      GGRC.WidgetList.get_current_page_widgets(),
      function (descriptor, name) {
        if (~newDefaultWidgets.indexOf(name)) {
          newWidgetDescriptors[name] = descriptor;
        }
      }
    );

    $.extend(
      true,
      newWidgetDescriptors,
      {
        info: {
          content_controller: GGRC.Controllers.InfoWidget,
          content_controller_options: {
            widget_view: GGRC.mustache_path +
              '/workflow_templates/info.mustache'
          }
        }
      }
    );

    new GGRC.WidgetList(
      'ggrc_workflows',
      {WorkflowTemplate: newWidgetDescriptors}
    );
  };

  workflowExtension.init_widgets_for_person_page = function () {
    var descriptor = {};
    var pageInstance = GGRC.page_instance();

    if (pageInstance) {
      descriptor[pageInstance.constructor.shortName] = {
      };
    }
    new GGRC.WidgetList('ggrc_workflows', descriptor, [
      'info_widget'
    ]);
  };

  workflowExtension.init_widgets_for_other_pages = function () {
    var descriptor = {};
    var pageInstance = GGRC.page_instance();

    if (pageInstance) {
      descriptor[pageInstance.constructor.shortName] = {
      };
    }
    new GGRC.WidgetList('ggrc_workflows', descriptor, [
      'info_widget'
    ]);
  };

  workflowExtension.init_widgets = function () {
    var pageInstance = GGRC.page_instance();

    if (pageInstance instanceof CMS.Models.WorkflowTemplate) {
      workflowExtension.init_widgets_for_workflow_page();
    } else if (pageInstance instanceof CMS.Models.Person) {
      workflowExtension.init_widgets_for_person_page();
    } else {
      workflowExtension.init_widgets_for_other_pages();
    }
  };

  GGRC.extensions.push(workflowExtension);
})(window.GGRC);

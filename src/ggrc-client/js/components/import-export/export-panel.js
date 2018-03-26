/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import template from './templates/export-panel.mustache';

let url = can.route.deparam(window.location.search.substr(1));
let filterModel = can.Map({
  model_name: 'Program',
  value: '',
  filter: {},
});

export default can.Component.extend({
  tag: 'export-panel',
  template,
  viewModel: {
    define: {
      showAttributes: {
        set: function (newValue, setValue) {
          this.updateIsSelected(
            this.attr('item.attributes'), newValue);

          setValue(newValue);
        },
      },
      showMappings: {
        set: function (newValue, setValue) {
          this.updateIsSelected(
            this.attr('item.mappings'), newValue);

          setValue(newValue);
        },
      },
      showLocalAttributes: {
        set: function (newValue, setValue) {
          this.updateIsSelected(
            this.attr('item.localAttributes'), newValue);

          setValue(newValue);
        },
      },
      panelNumber: {
        get() {
          return Number(this.attr('panel_index')) + 1;
        },
      },
    },
    exportable: GGRC.Bootstrap.exportable,
    snapshotable_objects: GGRC.config.snapshotable_objects,
    panel_index: '@',
    has_parent: false,
    removable: false,
    item: null,
    fetch_relevant_data: function (id, type) {
      let dfd = CMS.Models[type].findOne({id: id});
      dfd.then(function (result) {
        this.attr('item.relevant').push(new filterModel({
          model_name: url.relevant_type,
          value: url.relevant_id,
          filter: result,
        }));
      }.bind(this));
    },
    getModelAttributeDefenitions: function (type) {
      return GGRC.model_attr_defs[type];
    },
    useLocalAttribute: function () {
      return this.attr('item.type') === 'Assessment';
    },
    filterModelAttributes: function (attr, predicate) {
      return predicate &&
        !attr.import_only &&
        attr.display_name.indexOf('unmap:') === -1;
    },
    refreshItems: function () {
      let currentPanel = this.attr('item');
      let definitions = this
        .getModelAttributeDefenitions(currentPanel.attr('type'));
      let localAttributes;

      let attributes = _.filter(definitions, function (el) {
        return this.filterModelAttributes(el,
          el.type !== 'mapping' && el.type !== 'object_custom');
      }.bind(this));

      let mappings = _.filter(definitions, function (el) {
        return this.filterModelAttributes(el, el.type === 'mapping');
      }.bind(this));

      currentPanel.attr('attributes', attributes);
      currentPanel.attr('mappings', mappings);

      if (this.useLocalAttribute()) {
        localAttributes = _.filter(definitions, function (el) {
          return this.filterModelAttributes(el, el.type === 'object_custom');
        }.bind(this));

        currentPanel.attr('localAttributes', localAttributes);
      }
    },
    updateIsSelected: function (items, isSelected) {
      items.forEach(function (item) {
        item.attr('isSelected', isSelected);
      });
    },
    setSelected: function () {
      this.attr('showMappings', true);
      this.attr('showAttributes', true);

      if (this.useLocalAttribute()) {
        this.attr('showLocalAttributes', true);
      }
    },
  },
  events: {
    inserted: function () {
      let panelNumber = this.viewModel.attr('panelNumber');

      if (panelNumber === 1 && url.relevant_id && url.relevant_type) {
        this.viewModel.fetch_relevant_data(url.relevant_id, url.relevant_type);
      }
      this.viewModel.refreshItems();
      this.viewModel.setSelected();
    },
    '[data-action=select_toggle] click': function (el, ev) {
      let type = el.data('type');
      let value = el.data('value');
      let targetList;

      switch (type) {
        case 'local_attributes': {
          targetList = this.viewModel.attr('item.localAttributes');
          break;
        }
        case 'attributes': {
          targetList = this.viewModel.attr('item.attributes');
          break;
        }
        default: {
          targetList = this.viewModel.attr('item.mappings');
        }
      }

      this.viewModel.updateIsSelected(targetList, value);
    },
    '{viewModel} type': function (viewModel, ev, type) {
      viewModel.attr('item.relevant', []);
      viewModel.attr('item.filter', '');
      viewModel.attr('item.snapshot_type', '');
      viewModel.attr('item.has_parent', false);
      viewModel.attr('item.type', type);

      if (viewModel.attr('type') === 'Snapshot') {
        viewModel.attr('item.snapshot_type', 'Control');
      }

      viewModel.refreshItems();
      viewModel.setSelected();
    },
  },
});

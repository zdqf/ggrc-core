/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import './relevant-filter';
import './export-group';
import csvExportTemplate from './templates/csv-export.mustache';
import {confirm} from '../../plugins/utils/modals';
import {
  exportRequest,
  download,
  fileSafeCurrentDate,
} from './import-export-utils';
import {backendGdriveClient} from '../../plugins/ggrc-gapi-client';

can.Component.extend({
  tag: 'csv-export',
  template: csvExportTemplate,
  viewModel: {
    loading: false,
    fileName: 'export_objects.csv',
    chosenFormat: 'gdrive',
    panels: [],
    isFilterActive: false,
  },
  events: {
    toggleIndicator: function (currentFilter) {
      let isExpression =
          !!currentFilter &&
          !!currentFilter.expression.op &&
          currentFilter.expression.op.name !== 'text_search' &&
          currentFilter.expression.op.name !== 'exclude_text_search';
      this.viewModel.attr('isFilterActive', isExpression);
    },
    '.tree-filter__expression-holder input keyup': function (el, ev) {
      this.toggleIndicator(GGRC.query_parser.parse(el.val()));
    },
    '.option-type-selector change': function (el, ev) {
      this.viewModel.attr('isFilterActive', false);
    },
    getObjectsForExport: function () {
      let panels = this.viewModel.attr('panels');

      return _.map(panels, function (panel, index) {
        let relevantFilter;
        let predicates;
        let allItems = panel.attr('attributes')
          .concat(panel.attr('mappings'))
          .concat(panel.attr('localAttributes'));

        predicates = _.map(panel.attr('relevant'), function (el) {
          let id = el.model_name === '__previous__' ?
            index - 1 : el.filter.id;
          return id ? '#' + el.model_name + ',' + id + '#' : null;
        });
        if (panel.attr('snapshot_type')) {
          predicates.push(
            ' child_type = ' + panel.attr('snapshot_type') + ' '
          );
        }
        relevantFilter = _.reduce(predicates, function (p1, p2) {
          return p1 + ' AND ' + p2;
        });
        return {
          object_name: panel.type,
          fields: allItems
            .filter((item) => item.isSelected)
            .map((item) => item.key).serialize(),
          filters: GGRC.query_parser.join_queries(
            GGRC.query_parser.parse(relevantFilter || ''),
            GGRC.query_parser.parse(panel.filter || '')
          ),
        };
      });
    },
    '#export-csv-button click': function (el, ev) {
      this.viewModel.attr('loading', true);
      let data = {
        objects: this.getObjectsForExport(),
        export_to: this.viewModel.attr('chosenFormat'),
        current_time: fileSafeCurrentDate(),
      };

      backendGdriveClient.withAuth(()=> {
        return exportRequest({data});
      }).then((data, status, jqXHR)=> {
        let link;

        if (this.viewModel.attr('chosenFormat') === 'gdrive') {
          link = 'https://docs.google.com/spreadsheets/d/' + data.id;

          confirm({
            modal_title: 'Export Completed',
            modal_description: 'File is exported successfully. ' +
            'You can view the file here: ' +
            '<a href="' + link + '" target="_blank">' + link + '</a>',
            button_view: GGRC.mustache_path + '/modals/close_buttons.mustache',
          });
        } else {
          const contentDisposition =
            jqXHR.getResponseHeader('Content-Disposition');
          const match = contentDisposition.match(/filename\=(['"]*)(.*)\1/);
          const filename = match && match[2] || this.viewModel.attr('fileName');

          download(filename, data);
        }
      }, (xhr)=> {
        let message = (xhr.responseJSON && xhr.responseJSON.message) ?
          xhr.responseJSON.message :
          xhr.responseText;
        GGRC.Errors.notifier('error', message);
      }).always(()=> {
        this.viewModel.attr('export.loading', false);
      });
    },
  },
});

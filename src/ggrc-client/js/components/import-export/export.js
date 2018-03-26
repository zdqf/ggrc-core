/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import './relevant-filter';
import './export-group';
import csvExportTemplate from './templates/csv-export.mustache';
import {
  download,
  fileSafeCurrentDate,
  runExport,
  getExportsHistory,
  downloadExportContent,
  deleteExportJob,
  jobStatuses,
} from './import-export-utils';
import {backendGdriveClient} from '../../plugins/ggrc-gapi-client';
import './current-exports/current-exports';

const DEFAULT_TIMEOUT = 2000;

can.Component.extend({
  tag: 'csv-export',
  template: csvExportTemplate,
  viewModel: {
    isInProgress: false,
    loading: false,
    fileName: 'export_objects.csv',
    panels: [],
    isFilterActive: false,
    currentExports: [],
    timeout: DEFAULT_TIMEOUT,
    getInProgressJobs() {
      return this.attr('currentExports').filter((el) => {
        return el.status === jobStatuses.IN_PROGRESS;
      });
    },
    getExports(ids) {
      getExportsHistory(ids)
        .then((exports) => {
          const timeout = this.attr('timeout');
          if (ids) {
            let exportsMap = exports
              .reduce((map, job) => {
                map[job.id] = job.status;
                return map;
              }, {});

            this.attr('currentExports').forEach((job) => {
              if (exportsMap[job.id]) {
                job.attr('status', exportsMap[job.id]);
              }
            });
          } else {
            this.attr('currentExports').replace(exports);
          }
          if (this.getInProgressJobs().length) {
            this.attr('timeout', timeout * 2);
            this.attr('isInProgress', true);
            this.trackExportsStatus();
          } else {
            this.attr('isInProgress', false);
            this.attr('timeout', DEFAULT_TIMEOUT);
          }
        });
    },
    trackExportsStatus() {
      setTimeout(() => {
        let ids = this.getInProgressJobs().map((job) => job.id);
        this.getExports(ids);
      }, this.attr('timeout'));
    },
    onViewContent({id, format, fileName}) {
      if (format === 'csv') {
        downloadExportContent(id, format).then((data) => {
          download(fileName, data);
          this.onRemove({id});
        });
      } else if (format === 'gdrive') {
        backendGdriveClient.withAuth(() => {
          return downloadExportContent(id, format);
        }).then((data) => {
          let link = `https://docs.google.com/spreadsheets/d/${data.id}`;

          window.open(link, '_blank');

          this.onRemove({id});
        });
      }
    },
    onRemove({id}) {
      deleteExportJob(id)
        .then(() => {
          let index = _.findIndex(this.attr('currentExports'), {id});
          this.attr('currentExports').splice(index, 1);
        });
    },
    exportObjects() {
      let data = {
        objects: this.getObjectsForExport(),
        current_time: fileSafeCurrentDate(),
      };

      runExport(data)
        .then((jobInfo) => {
          const isInProgress = this.getInProgressJobs().length;
          this.attr('currentExports').push(jobInfo);
          this.attr('isInProgress', !!isInProgress);

          if (!isInProgress) {
            this.getExports([jobInfo.id]);
          }
        });
    },
    getObjectsForExport: function () {
      let panels = this.attr('panels');

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
  },
  events: {
    inserted() {
      this.viewModel.getExports();
    },
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
  },
});

/*
    Copyright (C) 2018 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import '../../plugins/utils/controllers';
import {
  jobStatuses,
  isStoppedJob,
  isInProgressJob,
  analyseBeforeImport,
  startImport,
  getImportJobInfo,
  getImportHistory,
  downloadContent,
  download,
} from './import-export-utils';
import '../show-more/show-more';
import '../import-export/download-template/download-template';
import '../collapsible-panel/collapsible-panel';
import '../confirm-action/confirm-action';
import quickTips from './templates/quick-tips.mustache';
import template from './templates/csv-import.mustache';
import {
  backendGdriveClient,
  gapiClient,
} from '../../plugins/ggrc-gapi-client';
import errorTemplate from './templates/import-error.mustache';

const messages = {
  INCORRECT_FORMAT: `The file is not in a recognized format. 
  Please import a Google sheet or a file in .csv format.`,
  EMPTY_FILE: 'You are going to import: <span class="gray">0 rows</span>',
  PLEASE_CONFIRM: `Please type "I confirm" below to confirm that 
  data being imported is complete and accurate. Please note importing 
  incomplete or accurate data can result in data corruption.`,
  IN_PROGRESS: `Your import request has been submitted. 
  You may close this page or continue your work. We will send you an email 
  notification when it completes or if there are errors or warnings.`,
  ANALYSIS_FAILED: `Your file could not be imported due to the following errors 
  that were found. You can download your file, fix the errors 
  and try importing again.`,
  FAILED: 'Import failed due to server error',
  FILE_STATS: (objects) => {
    const stats = Object.keys(objects).map((model) => {
      return `${objects[model]} ${model}`;
    }).join(', ');
    return `You are going to import: <span class="gray">${stats}</span>
      <div class="margin-top-20">${messages.PLEASE_CONFIRM}</div>`;
  },
};

export default can.Component.extend({
  tag: 'csv-import',
  template: template,
  requestData: null,
  viewModel: {
    define: {
      isImportStopped: {
        get() {
          return isStoppedJob(this.attr('state'));
        },
      },
      isDownloadTemplateAvailable: {
        get() {
          return ![
            jobStatuses.ANALYSIS,
            jobStatuses.IN_PROGRESS,
          ].includes(this.attr('state'));
        },
      },
    },
    quickTips,
    importDetails: null,
    fileId: '',
    fileName: '',
    isLoading: false,
    state: jobStatuses.SELECT,
    jobId: null,
    history: [],
    importStatus: '',
    message: '',
    processLoadedInfo: function (data) {
      let rows = 0;
      let errorLevel = '';
      this.attr('importDetails', _.map(data, (element) => {
        element.data = [];

        rows += element.rows;
        if (element.block_warnings.length + element.row_warnings.length) {
          let warnings = [...element.block_warnings, ...element.row_warnings];

          if (!errorLevel) {
            errorLevel = 'warning';
          }

          element.data.push({
            title: `WARNINGS (${warnings.length})`,
            messages: warnings,
          });
        }
        if (element.block_errors.length + element.row_errors.length) {
          let errors = [...element.block_errors, ...element.row_errors];

          errorLevel = 'error';

          this.attr('message', messages.ANALYSIS_FAILED);

          element.data.push({
            title: `ERRORS (${errors.length})`,
            messages: errors,
          });
        }
        return element;
      }));

      if (!rows) {
        this.attr('importStatus', 'error');
        this.attr('message', messages.EMPTY_FILE);
      } else {
        this.attr('importStatus', errorLevel);
      }
    },
    resetFile: function () {
      this.attr({
        state: jobStatuses.SELECT,
        fileId: '',
        fileName: '',
        importStatus: '',
        message: '',
      });
    },
    statusStrategies: {
      [jobStatuses.SELECT]() {},
      [jobStatuses.STOPPED]() {},
      [jobStatuses.NOT_STARTED]() {
        this.attr('message', messages.PLEASE_CONFIRM);
      },
      [jobStatuses.ANALYSIS](jobInfo, timeout) {
        this.attr('message', messages.IN_PROGRESS);
        this.trackStatusOfImport(jobInfo.id, timeout);
      },
      [jobStatuses.IN_PROGRESS](jobInfo, timeout) {
        this.attr('message', messages.IN_PROGRESS);
        this.trackStatusOfImport(jobInfo.id, timeout);
      },
      [jobStatuses.BLOCKED](jobInfo) {
        this.attr('message', '');
        this.processLoadedInfo(jobInfo.results);
      },
      [jobStatuses.ANALYSIS_FAILED](jobInfo) {
        this.attr('message', messages.ANALYSIS_FAILED);
        this.processLoadedInfo(jobInfo.results);
      },
      [jobStatuses.FAILED]() {
        this.attr('importStatus', 'error');
        this.attr('message', messages.FAILED);
      },
      [jobStatuses.FINISHED]() {
        this.resetFile();
        this.getImportHistory();
      },
    },
    analyseSelectedFile(file) {
      this.attr('isLoading', true);
      this.attr('fileId', file.id);
      this.attr('fileName', file.name);

      return backendGdriveClient.withAuth(()=> {
        return analyseBeforeImport(file.id);
      }, {responseJSON: {message: 'Unable to Authorize'}})
        .then((response) => {
          const counts = Object.values(response.objects);

          if (counts.some((number) => number > 0)) {
            this.attr('state', response.import_export.status);
            this.attr('message', messages.FILE_STATS(response.objects));
            this.attr('jobId', response.import_export.id);
          } else {
            this.attr('state', jobStatuses.SELECT);
            this.attr('importStatus', 'error');
            this.attr('message', messages.EMPTY_FILE);
          }
        }, (error) => {
          this.attr('state', jobStatuses.SELECT);
          this.attr('importStatus', 'error');

          if (error && error.responseJSON && error.responseJSON.message) {
            GGRC.Errors.notifier('error', error.responseJSON.message);
          } else {
            GGRC.Errors.notifier('error', errorTemplate, true);
          }
        });
    },
    onImportSubmit() {
      this.startImport(jobStatuses.ANALYSIS);
    },
    startImport(state) {
      this.attr('state', state);
      this.attr('message', messages.IN_PROGRESS);

      return startImport(this.attr('jobId'))
        .then((info) => {
          this.trackStatusOfImport(info.id);
        });
    },
    trackStatusOfImport(jobId, timeout = 2000) {
      setTimeout(() => {
        getImportJobInfo(jobId)
          .then((info) => {
            const strategy = this.attr('statusStrategies')[info.status]
              .bind(this);

            this.attr('state', info.status);

            strategy(info, timeout * 2);
          });
      }, timeout);
    },
    getImportHistory() {
      return getImportHistory()
        .then((imports) => {
          const lastJob = imports.length ? imports[imports.length - 1] : null;
          let completed = imports.filter((jobInfo) => {
            return jobInfo.status === jobStatuses.FINISHED;
          }).sort((a, b) => a.id < b.id ? 1 : -1);

          if (lastJob && isInProgressJob(lastJob.status)) {
            this.attr('fileName', lastJob.title || 'import_file.csv');
            this.attr('state', lastJob.status);
            this.attr('jobId', lastJob.id);
            this.trackStatusOfImport(lastJob.id);
          }

          this.attr('history').replace(completed);
        });
    },
    downloadImportContent() {
      downloadContent(this.attr('jobId'))
        .then((data) => {
          download(this.attr('fileName'), data);
        });
    },
    proceedWithWarnings() {
      if (this.attr('state') === jobStatuses.BLOCKED) {
        this.startImport(jobStatuses.IN_PROGRESS);
      }
    },
    selectFile() {
      let that = this;
      let allowedTypes = ['text/csv', 'application/vnd.google-apps.document',
        'application/vnd.google-apps.spreadsheet'];

      this.resetFile();

      return gapiClient.authorizeGapi(['https://www.googleapis.com/auth/drive'])
        .then(() => {
          gapi.load('picker', {callback: createPicker});
        });

      function createPicker() {
        let dialog;
        let docsUploadView;
        let docsView;
        let picker = new google.picker.PickerBuilder()
          .setOAuthToken(gapi.auth.getToken().access_token)
          .setDeveloperKey(GGRC.config.GAPI_KEY)
          .setCallback(pickerCallback);

        docsUploadView = new google.picker.DocsUploadView();
        docsView = new google.picker.DocsView()
          .setMimeTypes(allowedTypes);

        picker.addView(docsUploadView)
          .addView(docsView);

        picker = picker.build();
        picker.setVisible(true);

        $('div.picker-dialog-bg').css('zIndex', 4000);

        dialog = GGRC.Utils.getPickerElement(picker);
        if (dialog) {
          dialog.style.zIndex = 4001;
        }
      }

      function pickerCallback(data) {
        let file;
        let PICKED = google.picker.Action.PICKED;
        let ACTION = google.picker.Response.ACTION;
        let DOCUMENTS = google.picker.Response.DOCUMENTS;

        if (data[ACTION] === PICKED) {
          file = data[DOCUMENTS][0];

          if (file && _.any(allowedTypes, function (type) {
            return type === file.mimeType;
          })) {
            that.analyseSelectedFile(file);
          } else {
            that.attr('fileName', file.name);
            that.attr('importStatus', 'error');
            GGRC.Errors.notifier('error', messages.INCORRECT_FORMAT);
          }
        }
      }
    },
  },
  events: {
    inserted() {
      this.viewModel.getImportHistory();
    },
  },
});

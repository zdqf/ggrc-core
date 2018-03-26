/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import template from './current-exports.mustache';
import {jobStatuses} from '../import-export-utils';

export default can.Component.extend({
  tag: 'current-exports',
  template,
  viewModel: {
    exports: [],
    disabled: {},
    inProgress: false,
    tryAgain(id) {

    },
    remove(id) {
      if (!this.attr(`disabled.${id}`)) {
        this.dispatch({
          type: 'removeItem',
          id,
        });
      }
      this.attr(`disabled.${id}`, true);
    },
    downloadCSV(id, fileName) {
      this.dispatch({
        type: 'viewContent',
        format: 'csv',
        fileName,
        id,
      });
    },
    openSheet(id) {
      this.dispatch({
        type: 'viewContent',
        format: 'gdrive',
        id,
      });
    },
  },
  helpers: {
    canRemove(status, options) {
      let canRemove = [jobStatuses.FINISHED, jobStatuses.FAILED]
        .includes(status());

      return canRemove ?
        options.fn(options.contexts) :
        options.inverse(options.contexts);
    },
    isDisabled(id, options) {
      let isDisabled = this.attr(`disabled.${id()}`);

      return isDisabled ?
        options.fn(options.contexts) :
        options.inverse(options.contexts);
    },
  },
});

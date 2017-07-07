/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  GGRC.Components('repeatOnButtonWrapper', {
    tag: 'repeat-on-button-wrapper',
    template: '<repeat-on-button ' +
      '{unit}="instance.unit" ' +
      '{repeat-every}="instance.repeatEvery" ' +
      '{ends}="instance.ends" ' +
      '{occurrences}="instance.occurrences" ' +
      '(on-set-repeat)="onSetRepeat(%event)">' +
      '</repeat-on-button>',
    viewModel: {
      instance: {},
      onSetRepeat: function (event) {
        this.attr('instance.unit', event.unit);
        this.attr('instance.repeat_every', event.repeatEvery);
        this.attr('instance.ends', event.ends);
        this.attr('instance.occurrences', event.occurrences);
      }
    }
  });
})(window.can, window.GGRC);

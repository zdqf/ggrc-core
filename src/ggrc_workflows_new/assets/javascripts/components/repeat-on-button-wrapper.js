/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC, $) {
  'use strict';

  GGRC.Components('repeatOnButtonWrapper', {
    tag: 'repeat-on-button-wrapper',
    template: '<repeat-on-button ' +
      '{unit}="instance.unit" ' +
      '{repeat-every}="instance.repeat_every" ' +
      '{occurrences}="instance.occurrences" ' +
      '{on-save-repeat}="@onSetRepeat">' +
      '</repeat-on-button>',
    viewModel: {
      define: {
        autoSave: {
          type: 'boolean',
          value: false
        }
      },
      instance: {},
      setRepeatOn: function (unit, repeatEvery, occurrences) {
        this.attr('instance.unit', unit);
        this.attr('instance.repeat_every', repeatEvery);
        this.attr('instance.occurrences', occurrences);
      },
      updateRepeatOn: function () {
        var deferred = $.Deferred();
        var instance = this.attr('instance');

        instance.save()
          .done(function () {
            $(document.body).trigger('ajax:flash', {
              success: 'Repeat updated successfully'
            });
          })
          .fail(function () {
            $(document.body).trigger('ajax:flash', {
              error: 'An error occurred'
            });
          })
          .always(function () {
            deferred.resolve();
          });

        return deferred;
      },
      onSetRepeat: function (unit, repeatEvery, occurrences) {
        this.setRepeatOn(unit, repeatEvery, occurrences);
        if (this.attr('autoSave')) {
          return this.updateRepeatOn();
        }

        return $.Deferred().resolve();
      }
    }
  });
})(window.can, window.GGRC, window.can.$);

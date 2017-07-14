/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC, $) {
  'use strict';

  var template = can.view(GGRC.mustache_path +
    '/components/repeat-on-button.mustache');
  var config = GGRC.Workflow;
  var getEndOption = function (value) {
    return function (option) {
      return option.title.toLowerCase() === value;
    };
  };
  var neverEndOption = config.endOptions
    .find(getEndOption('never')).value;
  var afterEndOption = config.endOptions
      .find(getEndOption('after')).value;

  GGRC.Components('repeatOnButton', {
    tag: 'repeat-on-button',
    template: template,
    viewModel: {
      define: {
        buttonText: {
          get: function () {
            return this.getTitle(this.attr('unit'));
          }
        },
        modalTitle: {
          get: function () {
            return this.getTitle(this.attr('repeatEnabled'));
          }
        },
        repeatEnabled: {
          type: 'boolean',
          value: false
        },
        repeatDisabled: {
          get: function () {
            return !this.attr('repeatEnabled');
          }
        },
        repeatOptions: {
          Value: can.List
        },
        unitOptions: {
          Value: can.List
        },
        endOptions: {
          Value: can.List
        },
        shouldProvideOccurrences: {
          get: function () {
            return this.attr('repeatEnabled') &&
              this.attr('state.result.ends') !== neverEndOption;
          }
        },
        canSave: {
          type: 'boolean',
          value: true
        },
        isSaving: {
          type: 'boolean',
          value: false
        },
        onSaveRepeat: {
          value: function () {
            return function () {
              return $.Deferred().resolve();
            };
          }
        },
        ends: {
          get: function () {
            var occurrences = this.attr('occurrences');
            return occurrences ?
              afterEndOption :
              neverEndOption;
          }
        }
      },
      unit: null,
      repeatEvery: null,
      occurrences: null,
      state: {
        open: false,
        result: {
        }
      },
      getTitle: function (isEnabled) {
        return 'Repeat ' + (isEnabled ?
          'On' :
          'Off');
      },
      showDialog: function () {
        this.attr('state.open', true);
      },
      updateRepeatEveryOptions: function () {
        var selectedRepeatEvery;
        var repeatOptions = this.attr('repeatOptions');
        var unitOptions = this.attr('unitOptions');

        if (this.attr('state.result.unit')) {
          selectedRepeatEvery = _.find(unitOptions, function (option) {
            return option.value === this.attr('state.result.unit');
          }.bind(this));
          repeatOptions.forEach(function (option) {
            var unitName = option.value > 1 ?
              selectedRepeatEvery.plural :
              selectedRepeatEvery.singular;
            option.attr('title',
              option.value + ' ' + unitName);
          });
        }
      },
      initOptionLists: function () {
        this.attr('repeatOptions').replace(config.repeatOptions);
        this.attr('unitOptions').replace(config.unitOptions);
        this.attr('endOptions').replace(config.endOptions);
      },
      setResultOptions: function (unit, repeatEvery, ends, occurrences) {
        this.attr('state.result.unit', unit);
        this.attr('state.result.repeatEvery', repeatEvery);
        this.attr('state.result.ends', ends);
        this.attr('state.result.occurrences', occurrences);
      },
      setDefaultOptions: function () {
        this.setResultOptions(config.defaultRepeatValues.unit,
          config.defaultRepeatValues.repeatEvery,
          config.defaultRepeatValues.ends,
          config.defaultRepeatValues.occurrences);
      },
      initSelectedOptions: function () {
        var repeatEnabled = !!this.attr('unit');
        this.attr('repeatEnabled', repeatEnabled);

        this.setResultOptions(this.attr('unit'),
          this.attr('repeatEvery'),
          this.attr('ends'),
          this.attr('occurrences'));
      },
      init: function () {
        this.initSelectedOptions();
        this.initOptionLists();
        this.updateRepeatEveryOptions();
      },
      save: function () {
        var unit = null;
        var repeatEvery = null;
        var occurrences = null;
        var onSave = this.attr('onSaveRepeat');

        if (this.attr('repeatEnabled')) {
          unit = this.attr('state.result.unit');
          repeatEvery = this.attr('state.result.repeatEvery');
          occurrences = this.attr('state.result.occurrences');
        }

        this.attr('isSaving', true);
        onSave(unit, repeatEvery, occurrences)
          .then(function () {
            this.attr('isSaving', false);
            this.attr('state.open', false);
          }.bind(this));
      },
      checkOccurrences: function (event, element) {
        var occurrences = element[0].value;
        var canSave = !this.attr('shouldProvideOccurrences') ||
          (!!occurrences &&
            occurrences.match(/^\d+$/));

        this.attr('canSave', canSave);
      }
    },
    events: {
      '{state.result} unit': function () {
        this.viewModel.updateRepeatEveryOptions();
      },
      '{state.result} ends': function () {
        if (this.viewModel.attr('state.result.ends') ===
          neverEndOption) {
          this.viewModel.attr('state.result.occurrences', null);
        } else {
          this.viewModel.attr('state.result.occurrences',
            config.defaultRepeatValues.occurrences);
        }
      },
      '{viewModel} repeatEnabled': function () {
        if (!this.viewModel.attr('repeatEnabled')) {
          this.viewModel.attr('state.result.occurrences', null);
        } else if (!this.viewModel.attr('state.result.occurrences') &&
          this.viewModel.attr('state.result.ends') !== neverEndOption) {
          this.viewModel.attr('state.result.occurrences',
            config.defaultRepeatValues.occurrences);
        }
      },
      '{state} open': function () {
        if (this.viewModel.attr('state.open')) {
          this.viewModel.initSelectedOptions();
          if (!this.viewModel.attr('unit')) {
            this.viewModel.setDefaultOptions();
          }
        }
      }
    }
  });
})(window.can, window.GGRC, window.can.$);

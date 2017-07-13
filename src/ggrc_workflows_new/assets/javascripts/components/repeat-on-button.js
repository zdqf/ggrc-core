/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var template = can.view(GGRC.mustache_path +
    '/components/repeat-on-button.mustache');
  var neverEndOption = '0';

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
        }
      },
      unit: null,
      repeatEvery: null,
      ends: null,
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
        this.attr('repeatOptions').replace(GGRC.Workflow.repeatOptions);
        this.attr('unitOptions').replace(GGRC.Workflow.unitOptions);
        this.attr('endOptions').replace(GGRC.Workflow.endOptions);
      },
      setResultOptions: function (unit, repeatEvery, ends, occurrences) {
        this.attr('state.result.unit', unit);
        this.attr('state.result.repeatEvery', repeatEvery);
        this.attr('state.result.ends', ends);
        this.attr('state.result.occurrences', occurrences);
      },
      setDefaultOptions: function () {
        this.setResultOptions(GGRC.Workflow.defaultRepeatValues.unit,
          GGRC.Workflow.defaultRepeatValues.repeatEvery,
          GGRC.Workflow.defaultRepeatValues.ends,
          GGRC.Workflow.defaultRepeatValues.occurrences);
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
        var ends = null;

        if (this.attr('repeatEnabled')) {
          unit = this.attr('state.result.unit');
          repeatEvery = this.attr('state.result.repeatEvery');
          ends = this.attr('state.result.ends');
          occurrences = this.attr('state.result.occurrences');
        }

        this.dispatch({
          type: 'onSetRepeat',
          unit: unit,
          repeatEvery: repeatEvery,
          ends: ends,
          occurrences: occurrences
        });
        this.attr('state.open', false);
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
        if (this.viewModel.attr('state.result.ends') === neverEndOption) {
          this.viewModel.attr('state.result.occurrences', null);
        } else {
          this.viewModel.attr('state.result.occurrences',
            GGRC.Workflow.defaultRepeatValues.occurrences);
        }
      },
      '{viewModel} repeatEnabled': function () {
        if (!this.viewModel.attr('repeatEnabled')) {
          this.viewModel.attr('state.result.occurrences', null);
        } else if (!this.viewModel.attr('state.result.occurrences') &&
          this.viewModel.attr('state.result.ends') !== neverEndOption) {
          this.viewModel.attr('state.result.occurrences',
            GGRC.Workflow.defaultRepeatValues.occurrences);
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
})(window.can, window.GGRC);

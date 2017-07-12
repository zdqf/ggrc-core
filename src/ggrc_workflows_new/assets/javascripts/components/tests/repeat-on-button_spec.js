/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Components.repeatOnButton', function () {
  'use strict';

  var viewModel;
  var events;
  var neverEndOption = '0';
  var afterEndOption = '1';
  var getTitle = function (option) {
    return option.title;
  };

  beforeAll(function () {
    var Component = GGRC.Components.get('repeatOnButton');
    events = Component.prototype.events;
  });

  beforeEach(function () {
    viewModel = GGRC.Components.getViewModel('repeatOnButton');
  });

  describe('buttonText getter', function () {
    it('returns Off-indication when no unit was selected', function () {
      var result = viewModel.attr('buttonText');

      expect(result).toEqual('Repeat Off');
    });

    it('returns on-indication when unit was selected', function () {
      var result;
      viewModel.attr('unit', 'Day');

      result = viewModel.attr('buttonText');

      expect(result).toEqual('Repeat On');
    });
  });

  describe('modalTitle getter', function () {
    it('returns Off-indication when repeat was disabled', function () {
      var result = viewModel.attr('modalTitle');

      expect(result).toEqual('Repeat Off');
    });

    it('returns on-indication when repeat was enabled', function () {
      var result;
      viewModel.attr('repeatEnabled', true);

      result = viewModel.attr('modalTitle');

      expect(result).toEqual('Repeat On');
    });
  });

  describe('shouldProvideOccurrences method', function () {
    it('returns false when repeat was disabled', function () {
      var result = viewModel.attr('shouldProvideOccurrences');

      expect(result).toBeFalsy();
    });

    it('returns false when "Never" was selected from "Ends" options',
    function () {
      var result;
      viewModel.attr('repeatEnabled', true);
      viewModel.attr('state.result.ends', neverEndOption);

      result = viewModel.attr('shouldProvideOccurrences');

      expect(result).toBeFalsy();
    });

    it('returns false when "Never" was selected from "Ends" options',
    function () {
      var result;
      viewModel.attr('repeatEnabled', true);

      result = viewModel.attr('shouldProvideOccurrences');

      expect(result).toBeTruthy();
    });
  });

  describe('updateRepeatEveryOptions method', function () {
    var repeatOptions = [
      {
        value: 1,
        title: '1'
      },
      {
        value: 2,
        title: '2'
      }];
    var unitOptions = [
      {title: 'Daily', value: 'Day', plural: 'days', singular: 'day'},
      {title: 'Weekly', value: 'Week', plural: 'weeks', singular: 'week'},
      {title: 'Monthly', value: 'Month', plural: 'months', singular: 'month'}
    ];

    beforeEach(function () {
      viewModel.attr('repeatOptions', repeatOptions);
      viewModel.attr('unitOptions', unitOptions);
    });

    it('should not update options when unit was not selected',
    function () {
      var actualTitles;
      var expectedTitles = repeatOptions.map(getTitle);

      viewModel.updateRepeatEveryOptions();

      actualTitles = can.makeArray(viewModel.attr('repeatOptions'))
        .map(getTitle);
      expect(actualTitles).toEqual(expectedTitles);
    });

    it('should update options when unit was not selected',
    function () {
      var actualTitles;
      var expectedTitles = ['1 week', '2 weeks']
      viewModel.attr('state.result.unit', 'Week');

      viewModel.updateRepeatEveryOptions();

      actualTitles = can.makeArray(viewModel.attr('repeatOptions'))
        .map(getTitle);
      expect(actualTitles).toEqual(expectedTitles);
    });
  });

  describe('initSelectedOptions method', function () {
    it('should initialize values from injected properties',
    function () {
      var unit = 'Day';
      var repeatEvery = '2';
      var occurrences = 4;
      var ends = '1';
      viewModel.attr('unit', unit);
      viewModel.attr('repeatEvery', repeatEvery);
      viewModel.attr('occurrences', occurrences);
      viewModel.attr('ends', ends);

      viewModel.initSelectedOptions();

      expect(viewModel.attr('state.result.unit')).toEqual(unit);
      expect(viewModel.attr('state.result.repeatEvery')).toEqual(repeatEvery);
      expect(viewModel.attr('state.result.occurrences')).toEqual(occurrences);
      expect(viewModel.attr('state.result.ends')).toEqual(ends);
      expect(viewModel.attr('repeatEnabled')).toBeTruthy();
    });
  });

  describe('init method', function () {
    it('should initialize values from injected properties',
    function () {
      var unit = 'Day';
      var repeatEvery = '2';
      var occurrences = 4;
      var ends = '1';
      viewModel.attr('unit', unit);
      viewModel.attr('repeatEvery', repeatEvery);
      viewModel.attr('occurrences', occurrences);
      viewModel.attr('ends', ends);

      viewModel.init();

      expect(viewModel.attr('state.result.unit')).toEqual(unit);
      expect(viewModel.attr('state.result.repeatEvery')).toEqual(repeatEvery);
      expect(viewModel.attr('state.result.occurrences')).toEqual(occurrences);
      expect(viewModel.attr('state.result.ends')).toEqual(ends);
      expect(viewModel.attr('repeatEnabled')).toBeTruthy();
    });
  });

  describe('save method', function () {
    beforeEach(function () {
      spyOn(viewModel, 'dispatch');
    });

    it('should notify with selected values when repeat is enabled',
    function () {
      var unit = 'Day';
      var repeatEvery = '2';
      var occurrences = 4;
      var ends = '1';
      viewModel.attr('state.result.unit', unit);
      viewModel.attr('state.result.repeatEvery', repeatEvery);
      viewModel.attr('state.result.occurrences', occurrences);
      viewModel.attr('state.result.ends', ends);
      viewModel.attr('repeatEnabled', true);

      viewModel.save();

      expect(viewModel.dispatch).toHaveBeenCalledWith({
        type: 'onSetRepeat',
        unit: unit,
        repeatEvery: repeatEvery,
        ends: ends,
        occurrences: occurrences
      });
      expect(viewModel.attr('state.open')).toBeFalsy();
    });

    it('should notify with empty values when repeat is disabled',
    function () {
      viewModel.save();

      expect(viewModel.dispatch).toHaveBeenCalledWith({
        type: 'onSetRepeat',
        unit: null,
        repeatEvery: null,
        ends: null,
        occurrences: null
      });
      expect(viewModel.attr('state.open')).toBeFalsy();
    });
  });

  describe('checkOccurrences method', function () {
    it('should allow saving when should not provide occurrences',
    function () {
      var elements = [{value: '-1'}];
      viewModel.attr('repeatEnabled', false);

      viewModel.checkOccurrences(null, elements);

      expect(viewModel.attr('canSave')).toBeTruthy();
    });

    it('should disable saving when should provide occurrences' +
      ' and negative value',
    function () {
      var elements = [{value: '-1'}];
      viewModel.attr('repeatEnabled', true);

      viewModel.checkOccurrences(null, elements);

      expect(viewModel.attr('canSave')).toBeFalsy();
    });

    it('should disable saving when should provide occurrences' +
      ' and invalid value',
    function () {
      var elements = [{value: 'ab'}];
      viewModel.attr('repeatEnabled', true);

      viewModel.checkOccurrences(null, elements);

      expect(viewModel.attr('canSave')).toBeFalsy();
    });

    it('should disable saving when should provide occurrences' +
      ' and valid value',
    function () {
      var elements = [{value: '23'}];
      viewModel.attr('repeatEnabled', true);

      viewModel.checkOccurrences(null, elements);

      expect(viewModel.attr('canSave')).toBeTruthy();
    });
  });

  describe('unit update event', function () {
    var unitChanged;
    var context;
    var repeatOptions = [
      {
        value: 1,
        title: '1'
      },
      {
        value: 2,
        title: '2'
      }];

    beforeAll(function () {
      unitChanged = events['{state.result} unit'];
      viewModel.attr('repeatOptions', repeatOptions);
      context = {
        viewModel: viewModel
      };
    });

    it('should update repeat options when unit changed',
    function () {
      var actualTitles;
      var expectedTitles = ['1 day', '2 days'];
      context.viewModel.attr('state.result.unit', 'Day');

      unitChanged.apply(context);

      actualTitles = can.makeArray(context.viewModel.attr('repeatOptions'))
        .map(getTitle);
      expect(actualTitles).toEqual(expectedTitles);
    });
  });

  describe('ends update event', function () {
    var endsChanged;
    var context;

    beforeAll(function () {
      endsChanged = events['{state.result} ends'];
      context = {
        viewModel: viewModel
      };
    });

    it('should reset occurrences when "Never" option selected',
    function () {
      context.viewModel.attr('state.result.ends', neverEndOption);

      endsChanged.apply(context);

      expect(context.viewModel.attr('state.result.occurrences'))
        .toBeNull();
    });

    it('should set default value for occurrences when "After" option selected',
    function () {
      context.viewModel.attr('state.result.ends', afterEndOption);

      endsChanged.apply(context);

      expect(context.viewModel.attr('state.result.occurrences'))
        .toEqual('10');
    });
  });

  describe('repeatEnabled update event', function () {
    var repeatChanged;
    var context;

    beforeAll(function () {
      repeatChanged = events['{viewModel} repeatEnabled'];
      context = {
        viewModel: viewModel
      };
    });

    it('should reset occurrences when repeat was unchecked',
    function () {
      context.viewModel.attr('repeatEnabled', false);

      repeatChanged.apply(context);

      expect(context.viewModel.attr('state.result.occurrences'))
        .toBeNull();
    });

    it('should not update occurrences when repeat was checked ' +
      'but occurrences was set previously',
    function () {
      var expectedOccurrences = '12';
      context.viewModel.attr('repeatEnabled', true);
      context.viewModel.attr('state.result.occurrences', expectedOccurrences);

      repeatChanged.apply(context);

      expect(context.viewModel.attr('state.result.occurrences'))
        .toEqual(expectedOccurrences);
    });

    it('should not update occurrences when repeat was checked ' +
      'but "Never" end option was selected',
    function () {
      var expectedOccurrences = '12';
      context.viewModel.attr('repeatEnabled', true);
      context.viewModel.attr('state.result.ends', neverEndOption);

      repeatChanged.apply(context);

      expect(context.viewModel.attr('state.result.occurrences'))
        .toEqual(expectedOccurrences);
    });

    it('should not update occurrences when repeat was checked ' +
      'but "After" end option was selected',
    function () {
      context.viewModel.attr('repeatEnabled', true);
      context.viewModel.attr('state.result.ends', afterEndOption);
      context.viewModel.attr('state.result.occurrences', null);

      repeatChanged.apply(context);

      expect(context.viewModel.attr('state.result.occurrences'))
        .toEqual('10');
    });
  });

  describe('open update event', function () {
    var openChanged;
    var context;

    beforeAll(function () {
      openChanged = events['{state} open'];
      context = {
        viewModel: viewModel
      };
    });

    it('should set saved values for options when modal with unit opens',
    function () {
      var unit = 'Day';
      var repeatEvery = '2';
      var occurrences = 4;
      var ends = '1';
      context.viewModel.attr('state.open', true);
      context.viewModel.attr('unit', unit);
      context.viewModel.attr('repeatEvery', repeatEvery);
      context.viewModel.attr('occurrences', occurrences);
      context.viewModel.attr('ends', ends);
      context.viewModel.attr('state.result.ends', afterEndOption);

      openChanged.apply(context);

      expect(context.viewModel.attr('state.result.unit'))
        .toEqual(unit);
      expect(context.viewModel.attr('state.result.repeatEvery'))
        .toEqual(repeatEvery);
      expect(context.viewModel.attr('state.result.occurrences'))
        .toEqual(occurrences);
      expect(context.viewModel.attr('state.result.ends'))
        .toEqual(ends);
      expect(context.viewModel.attr('repeatEnabled'))
        .toBeTruthy();
    });

    it('should set default values for options when modal without unit opens',
    function () {
      context.viewModel.attr('state.open', true);
      context.viewModel.attr('unit', null);
      context.viewModel.attr('repeatEvery', 0);
      context.viewModel.attr('occurrences', '8');
      context.viewModel.attr('ends', 1);
      context.viewModel.attr('state.result.ends', afterEndOption);

      openChanged.apply(context);

      expect(context.viewModel.attr('state.result.unit')).toEqual('Month');
      expect(context.viewModel.attr('state.result.repeatEvery')).toEqual(1);
      expect(context.viewModel.attr('state.result.occurrences')).toEqual('10');
      expect(context.viewModel.attr('state.result.ends')).toEqual(0);
    });
  });
});

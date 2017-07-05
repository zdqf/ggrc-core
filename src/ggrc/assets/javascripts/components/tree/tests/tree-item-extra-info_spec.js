/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Components.treeItemExtraInfo', function () {
  'use strict';

  var viewModel;
  var activeModel = ['Regulation', 'Contract', 'Policy', 'Standard', 'Section'];

  beforeEach(function () {
    viewModel = GGRC.Components.getViewModel('treeItemExtraInfo');
  });

  describe('is active if', function () {
    it('workflow_state is defined', function () {
      viewModel.attr('instance', {workflow_state: 'far'});
      expect(viewModel.attr('isActive')).toBeTruthy();
    });

    activeModel.forEach(function (model) {
      it('instance is ' + model, function () {
        viewModel.attr('instance', new CMS.Models[model]());
        expect(viewModel.attr('isActive')).toBeTruthy();
      });
    });
  });

  describe('is not active if', function () {
    var allModels = Object.keys(GGRC.tree_view.attr('base_widgets_by_type'));
    var notActiveModels = _.difference(allModels, activeModel);

    it('workflow_state is not defined', function () {
      viewModel.attr('instance', {title: 'FooBar'});
      expect(viewModel.attr('isActive')).toBeFalsy();
    });

    notActiveModels.forEach(function (model) {
      if (CMS.Models[model]) {
        it('instance is ' + model, function () {
          viewModel.attr('instance', new CMS.Models[model]());
          expect(viewModel.attr('isActive')).toBeFalsy();
        });
      }
    });
  });

  describe('isOverdue property', function () {
    it('returns true if workflow_status is "Overdue"', function () {
      var result;
      viewModel.attr('instance', {
        workflow_state: 'Overdue'
      });

      result = viewModel.attr('isOverdue');

      expect(result).toBe(true);
    });
  });
});

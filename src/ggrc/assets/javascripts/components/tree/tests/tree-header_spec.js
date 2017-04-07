/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Components.treeHeader', function () {
  'use strict';

  var vm;

  function generateColumns(names) {
    return names.map(function (name) {
      return {
        attr_name: name
      }
    });
  }

  beforeEach(function () {
    vm = GGRC.Components.getViewModel('treeHeader');
  });

  describe('setColumns() method', function () {
    var method;
    beforeEach(function () {
      method = vm.setColumns.bind(vm);
    });

    it('dispatches "updateColumns" event with selected columns', function () {
      vm.attr('columns', {
        col1: true,
        col2: false,
        col3: true,
        col4: true,
        col5: false,
        col6: true
      });

      spyOn(vm, 'dispatch');

      method();

      expect(vm.dispatch).toHaveBeenCalledWith({
        type: 'updateColumns',
        columns: ['col1', 'col3', 'col4', 'col6']
      });
    });
  });

  describe('initializeColumns() method', function () {
    var method;
    beforeEach(function () {
      method = vm.initializeColumns.bind(vm);
    });

    it('dispatches "updateColumns" event with selected columns', function () {
      vm.attr('availableColumns',
        generateColumns(['col1', 'col2', 'col3', 'col4','col5']));
      vm.attr('selectedColumns', generateColumns(['col1', 'col3']));

      method();

      expect(vm.attr('columns').serialize()).toEqual({
        col1: true,
        col2: false,
        col3: true,
        col4: false,
        col5: false
      });
    });
  });
});

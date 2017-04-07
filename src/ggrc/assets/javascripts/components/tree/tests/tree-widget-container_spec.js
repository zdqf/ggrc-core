/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Components.treeWidgetContainer', function () {
  'use strict';

  var vm;

  beforeEach(function () {
    vm = GGRC.Components.getViewModel('treeWidgetContainer');
  });

  describe('getDepthFilter() method', function () {
    var getDepthFilter;
    beforeEach(function () {
      getDepthFilter = vm.getDepthFilter.bind(vm);
    });

    it('returns just filter where depth = true', function () {
      var result;

      vm.attr('filters', [{
        filter: 'filter1',
        depth: true
      }, {
        filter: 'filter2'
      }]);

      result = getDepthFilter();

      expect(result).toEqual('filter1');
    });

    it('returns concatenation of depth filters', function () {
      var result;

      vm.attr('filters', [{
        filter: 'filter1',
        depth: true
      }, {
        filter: 'filter2'
      },{
        filter: 'filter3',
        depth: true
      }]);

      result = getDepthFilter();

      expect(result).toEqual('filter1 AND filter3');
    });


    it('returns concatenation of depth filters with specified operation',
      function () {
        var result;

        vm.attr('filters', [{
          filter: 'filter1',
          depth: true
        }, {
          filter: 'filter2'
        },{
          filter: 'filter3',
          depth: true,
          operation: 'OR'
        }]);

        result = getDepthFilter();

        expect(result).toEqual('filter1 OR filter3');
      });
  });

  describe('currentFilter property', function () {
    it('returns concatenation of active filters', function () {
      var result;

      vm.attr('filters', [{
        filter: 'filter1',
        depth: true
      }, {
        filter: 'filter2'
      }, {
        filter: ''
      }]);

      result = vm.attr('currentFilter');

      expect(result).toEqual('filter1 AND filter2');
    });

    it('returns concatenation of active filters with specified operation',
      function () {
        var result;

        vm.attr('filters', [{
          filter: 'filter1',
          depth: true
        }, {
          filter: 'filter2'
        },{
          filter: 'filter3',
          depth: true,
          operation: 'OR'
        }]);

        result = vm.attr('currentFilter');

        expect(result).toEqual('filter1 AND filter2 OR filter3');
      });

    it('returns concatenation of active filters with specified operation and' +
      'add active additional filter',
      function () {
        var result;

        vm.attr('additionalFilter', 'me too');

        vm.attr('filters', [{
          filter: 'filter1',
          depth: true
        }, {
          filter: 'filter2'
        },{
          filter: 'filter3',
          depth: true,
          operation: 'OR'
        }]);

        result = vm.attr('currentFilter');

        expect(result).toEqual('me too AND filter1 AND filter2 OR filter3');
      });
  });

  describe('onSort() method', function () {
    var onSort;

    beforeEach(function () {
      onSort = vm.onSort.bind(vm);

      spyOn(vm, 'loadItems');
    });

    it('sets current order properties', function () {
      onSort({
        field: 'col1'
      });

      expect(vm.attr('sortingInfo.sortBy')).toEqual('col1');
      expect(vm.attr('sortingInfo.sortDirection')).toEqual('desc');
      expect(vm.attr('pageInfo.current')).toEqual(1);
      expect(vm.loadItems).toHaveBeenCalled();
    });

    it('changes sortDirection for current column', function () {
      vm.attr('sortingInfo', {
        sortBy: 'field',
        sortDirection: 'desc'
      });
      onSort({
        field: 'field'
      });

      expect(vm.attr('sortingInfo.sortBy')).toEqual('field');
      expect(vm.attr('sortingInfo.sortDirection')).toEqual('asc');
      expect(vm.attr('pageInfo.current')).toEqual(1);
      expect(vm.loadItems).toHaveBeenCalled();
    });

    it('changes sortBy property', function () {
      vm.attr('sortingInfo', {
        sortBy: 'field1',
        sortDirection: 'asc'
      });
      onSort({
        field: 'newField'
      });

      expect(vm.attr('sortingInfo.sortBy')).toEqual('newField');
      expect(vm.attr('sortingInfo.sortDirection')).toEqual('desc');
      expect(vm.attr('pageInfo.current')).toEqual(1);
      expect(vm.loadItems).toHaveBeenCalled();
    });
  });

  describe('loadItems() method', function () {
    var loadItems;

    beforeEach(function () {
      vm.attr({
        model: {shortName: 'modelName'},
        options: {
          parent_instance: {}
        }
      });
      loadItems = vm.loadItems.bind(vm);
    });

    it('', function (done) {
      spyOn(GGRC.Utils.TreeView, 'loadFirstTierItems')
        .and.returnValue(can.Deferred().resolve({
          total: 100,
          values: []
        }));

      loadItems().then(function () {
        expect(vm.attr('pageInfo.total')).toEqual(100);
        expect(can.makeArray(vm.attr('showedItems'))).toEqual([]);
        done();
      });
    })
  });
});

/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Components.subTreeWrapper', function () {
  'use strict';

  var vm;

  beforeEach(function () {
    vm = GGRC.Components.getViewModel('subTreeWrapper');
    vm.getDepthFilter = function () {
      return '';
    };
  });

  describe('loadItems() method', function () {
    var method;
    beforeEach(function () {
      vm.attr('parent', {
        type: 'Foo',
        id: 13
      });

      method = vm.loadItems.bind(vm);
    });

    it('doesnt call server-side if childModels not defined', function (done) {
      spyOn(GGRC.Utils.TreeView, 'loadItemsForSubTier');

      method().then(function () {
        expect(GGRC.Utils.TreeView.loadItemsForSubTier).not.toHaveBeenCalled();

        done();
      });
    });

    it('returns empty list', function (done) {
      vm.attr('childModels', ['a', 'b', 'c']);
      spyOn(GGRC.Utils.TreeView, 'loadItemsForSubTier').and
        .returnValue(can.Deferred().resolve({
          directlyItems: [],
          notDirectlyItems: [],
          showMore: false
        }));

      method().then(function () {
        expect(vm.attr('loading')).toBeFalsy();
        expect(vm.attr('directlyItems').length).toEqual(0);
        expect(vm.attr('notDirectlyItems').length).toEqual(0);
        expect(vm.attr('showMore')).toBeFalsy();
        expect(vm.attr('dataIsReady')).toBeTruthy();
        expect(vm.attr('notResult')).toBeTruthy();

        done();
      });
    });

    it('returns valid data from server-side', function (done) {
      vm.attr('childModels', ['a', 'b', 'c']);
      spyOn(GGRC.Utils.TreeView, 'loadItemsForSubTier').and
        .returnValue(can.Deferred().resolve({
          directlyItems: [1, 2, 3],
          notDirectlyItems: [4, 5, 6, 7],
          showMore: false
        }));

      method().then(function () {
        expect(vm.attr('loading')).toBeFalsy();
        expect(vm.attr('directlyItems').length).toEqual(3);
        expect(vm.attr('notDirectlyItems').length).toEqual(4);
        expect(vm.attr('showMore')).toBeFalsy();
        expect(vm.attr('dataIsReady')).toBeTruthy();
        expect(vm.attr('notResult')).toBeFalsy();

        done();
      });
    });
  });
});

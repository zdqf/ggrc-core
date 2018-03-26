/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import Component from './confirm-action';
import {getComponentVM} from '../../../js_specs/spec_helpers';

describe('confirm-action component', () => {
  let vm;

  beforeEach(() => {
    vm = getComponentVM(Component);
  });

  describe('submit() method', () => {
    it('dispatch should not be called for invalid state', () => {
      spyOn(vm, 'dispatch');

      vm.submit();
      expect(vm.dispatch).not.toHaveBeenCalled();
    });

    it('dispatch should be called for valid state', () => {
      spyOn(vm, 'dispatch');

      vm.attr('isValid', true);

      vm.submit();
      expect(vm.dispatch).toHaveBeenCalledWith('onConfirm');
    });
  });
});

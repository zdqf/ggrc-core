/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import '../../../related-objects/related-documents';
import '../../../object-list/object-list';
import '../../../object-list-item/editable-document-object-list-item';
import '../../../unmap-button/unmap-button';

import CTCommentHelpers from '../utils/cycle-task-comments-utils';

import template from './templates/cycle-task-comments-item.mustache';

const viewModel = can.Map.extend({
  parentInstance: {}, // CycleTask
  instance: {}, // Comment
  async removeComment() {
    const instance = this.attr('instance');
    await CTCommentHelpers.removeComment(instance);
    this.dispatch('removed');
  },
});

export default GGRC.Components('cycleTaskCommentsItem', {
  tag: 'cycle-task-comments-item',
  template,
  viewModel,
});

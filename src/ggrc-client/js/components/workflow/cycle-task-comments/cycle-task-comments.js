/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import './cycle-task-comments-item/cycle-task-comments-item';

import template from './templates/cycle-task-comments.mustache';

const viewModel = can.Map.extend({
  comments: [],
  instance: {},
});

export default GGRC.Components('cycleTaskComments', {
  tag: 'cycle-task-comments',
  template,
  viewModel,
});

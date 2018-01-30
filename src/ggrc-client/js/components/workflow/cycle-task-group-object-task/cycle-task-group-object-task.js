/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import template from './templates/cycle-task-group-object-task.mustache';
import '../../object-change-state/object-change-state';
import '../../dropdown/dropdown';
import '../cycle-task-comments/cycle-task-comments';
import RefreshQueue from '../../../models/refresh_queue';

let viewModel = can.Map.extend({
  showLink: function () {
    let pageInstance = GGRC.page_instance();

    return pageInstance.type !== 'Workflow';
  },
  instance: {},
  cycleTaskEntries: [],
  initialState: 'Assigned',
  cycle: {},
  workflow: {},
  async init() {
    const cycle = await this.loadCycle();
    await this.loadWorkflow(cycle);
    await this.loadCycleTaskEntries();
  },
  async loadCycleTaskEntries() {
    const instance = this.attr('instance');
    const ctEntries = instance.attr('cycle_task_entries');
    await instance.refresh_all('cycle_task_entries');
    this.attr('cycleTaskEntries', ctEntries.reify());
  },
  loadCycle: function () {
    let stubCycle = this.attr('instance.cycle').reify();
    let dfdResult;

    if (!_.isEmpty(stubCycle)) {
      dfdResult = new RefreshQueue()
        .enqueue(stubCycle)
        .trigger()
        .then(_.first)
        .then(function (cycle) {
          this.attr('cycle', cycle);
          return cycle;
        }.bind(this));
    } else {
      dfdResult = can.Deferred().reject();
    }

    return dfdResult;
  },
  loadWorkflow: function (cycle) {
    const workflowStub = cycle.attr('workflow');
    let workflow;

    // if a user doesn't have permissions to read the workflow
    if (!workflowStub) {
      const workflow = this.buildTrimmedWorkflowObject();
      this.attr('workflow', workflow);
      return;
    }

    workflow = workflowStub.reify();
    return new RefreshQueue().enqueue(workflow)
      .trigger()
      .then(_.first)
      .then(function (loadedWorkflow) {
        this.attr('workflow', loadedWorkflow);
      }.bind(this));
  },
  /**
   * Returns workflow object with trimmed data.
   * @return {can.Map} - trimmed workflow.
   */
  buildTrimmedWorkflowObject() {
    const instance = this.attr('instance');
    const workflow = new can.Map({
      viewLink: this.buildWorkflowLink(),
      title: instance.attr('workflow_title'),
    });
    return workflow;
  },
  buildWorkflowLink() {
    const instance = this.attr('instance');
    const id = instance.attr('workflow.id');
    return `/workflows/${id}`;
  },
  onStateChange: function (event) {
    let instance = this.attr('instance');
    let newStatus = event.state;

    instance.refresh()
      .then(function (refreshed) {
        refreshed.attr('status', newStatus);
        return refreshed.save();
      });
  },
});

export default GGRC.Components('cycleTaskGroupObjectTask', {
  tag: 'cycle-task-group-object-task',
  template: template,
  viewModel: viewModel,
});

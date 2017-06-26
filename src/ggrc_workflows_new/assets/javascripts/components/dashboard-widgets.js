/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (GGRC, can, $) {
  GGRC.Components('dashboardWidgets', {
    tag: 'dashboard-widgets',
    template: '<content/>',
    viewModel: {
      initialWfSize: 5,
      workflowView: GGRC.mustache_path +
        '/dashboard/workflow_progress.mustache',
      workflowData: {},
      workflowCount: 0,
      workflowShowAll: false
    },
    events: {
      // Click action to show all workflows
      'a.workflow-trigger.show-all click': function (el, ev) {
        var data = this.scope.workflowData;
        data.attr('list', data.currentWfs);

        el.text('Show top 5 workflows');
        el.removeClass('show-all');
        el.addClass('show-5');

        ev.stopPropagation();
      },
      // Show only top 5 workflows
      'a.workflow-trigger.show-5 click': function (el, ev) {
        var data = this.scope.workflowData;
        data.attr('list', data.top5Wfs);

        el.text('Show all my workflows');
        el.removeClass('show-5');
        el.addClass('show-all');

        ev.stopPropagation();
      },
      // Show Workflows
      'li.workflow-tab click': function (el, ev) {
        el.addClass('active');
        this.element.find('.workflow-wrap-main').show();
        ev.stopPropagation();
      }
    },
    init: function () {
      this.initMyWorkflows();
    },
    initMyWorkflows: function () {
      var self = this;
      var workflowData = {};
      var wfs;
      var currentWfs;
      var top5Wfs;

      if (!GGRC.current_user) {
        return;
      }

      GGRC.Models.Search.search_for_types('', ['Workflow'],
        {contact_id: GGRC.current_user.id})
        .then(function (resultSet) {
          var wfData = resultSet.getResultsForType('Workflow');
          var refreshQueue = new RefreshQueue();
          refreshQueue.enqueue(wfData);
          return refreshQueue.trigger();
        })
        .then(function (options) {
          wfs = options;

          return $.when.apply($, can.map(options, function (wf) {
            return self.updateTasksForWorkflow(wf);
          }));
        })
        .then(function () {
          if (wfs.length > 0) {
            // Filter workflows with a current cycle
            currentWfs = self.filterCurrentWorkflows(wfs);
            self.scope.attr('workflowCount', currentWfs.length);
            // Sort the workflows in ascending order by firstEndDate
            currentWfs.sort(self.sortByEndDate);
            workflowData.currentWfs = currentWfs;

            if (currentWfs.length > self.scope.initialWfSize) {
              top5Wfs = currentWfs.slice(0, self.scope.initialWfSize);
              self.scope.attr('workflow_show_all', true);
            } else {
              top5Wfs = currentWfs;
              self.scope.attr('workflow_show_all', false);
            }

            workflowData.top5Wfs = top5Wfs;
            workflowData.list = top5Wfs;
            self.scope.attr('workflowData', workflowData);
          }
        });

      return 0;
    },
    updateTasksForWorkflow: function (workflow) {
      var dfd = $.Deferred();
      var taskCount = 0;
      var finished = 0;
      var inProgress = 0;
      var declined = 0;
      var verified = 0;
      var assigned = 0;
      var overdue = 0;
      var today = new Date();
      var firstEndDate;
      var taskData = {};

      workflow.get_binding('current_all_tasks')
        .refresh_instances()
        .then(function (tasks) {
          var myData = tasks;
          var data;
          var endDate;
          var timeInterval;
          var dayInMilliSecs;
          var i;
          taskCount = myData.length;
          for (i = 0; i < taskCount; i++) {
            data = myData[i].instance;
            endDate = new Date(data.end_date || null);

            // Calculate first_end_date for the workflow / earliest end for all the tasks in a workflow
            if (i === 0) {
              firstEndDate = endDate;
            } else if (endDate.getTime() < firstEndDate.getTime()) {
              firstEndDate = endDate;
            }

            // Any task not verified is subject to overdue
            if (data.status === 'Verified') {
              verified++;
            } else if (data.isOverdue) {
              overdue++;
              $('dashboard-errors')
                .control()
                .scope
                .attr('errorMessage', 'Some tasks are overdue!');
            } else if (data.status === 'Finished') {
              finished++;
            } else if (data.status === 'InProgress') {
              inProgress++;
            } else if (data.status === 'Declined') {
              declined++;
            } else {
              assigned++;
            }
          }
          // Update Task_data object for workflow and Calculate %
          if (taskCount > 0) {
            taskData.taskCount = taskCount;
            taskData.finished = finished;
            taskData.finishedPercentage =
              (finished * 100 / taskCount).toFixed(2);
            taskData.inProgress = inProgress;
            taskData.inProgressPercentage =
              (inProgress * 100 / taskCount).toFixed(2);
            taskData.verified = verified;
            taskData.verifiedPercentage =
              (verified * 100 / taskCount).toFixed(2);
            taskData.declined = declined;
            taskData.declinedPercentage =
              (declined * 100 / taskCount).toFixed(2);
            taskData.overdue = overdue;
            taskData.overduePercentage =
              (overdue * 100 / taskCount).toFixed(2);
            taskData.assigned = assigned;
            taskData.assignedPercentage =
              (assigned * 100 / taskCount).toFixed(2);
            taskData.firstEndDateD = firstEndDate;
            taskData.firstEndDate = firstEndDate.toLocaleDateString();

            // calculate days left for first_end_date
            if (today.getTime() >= firstEndDate.getTime()) {
              taskData.daysLeftForFirstTask = 0;
            } else {
              timeInterval = firstEndDate.getTime() - today.getTime();
              dayInMilliSecs = 24 * 60 * 60 * 1000;
              taskData.daysLeftForFirstTask =
                Math.floor(timeInterval / dayInMilliSecs);
            }

            // set overdue flag
            taskData.overdueFlag = !!overdue;
          }

          workflow.attr('taskData', new can.Map(taskData));
          dfd.resolve();
        });

      return dfd;
    },
    /*
      filterCurrentWorkflows filters the workflows with current tasks in a
      new array and returns the new array.
      filterCurrentWorkflows should be called after update_tasks_for_workflow.
      It looks at the taskData.taskCount for each workflow
      For workflow with current tasks, taskData.taskCount must be > 0;
    */
    filterCurrentWorkflows: function (workflows) {
      var filteredWfs = [];

      can.each(workflows, function (item) {
        if (item.taskData) {
          if (item.taskData.taskCount > 0) {
            filteredWfs.push(item);
          }
        }
      });
      return filteredWfs;
    },
    /*
      sort_by_end_date sorts workflows in assending order with respect to task_data.first_end_date
      This should be called with workflows with current tasks.
    */
    sortByEndDate: function (a, b) {
      return (a.taskData.firstEndDateD.getTime() -
        b.taskData.firstEndDateD.getTime());
    }
  });
})(window.GGRC, window.can, window.can.$);

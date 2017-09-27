# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Set valid start_date and end_dates for annually

Create Date: 2017-09-27 13:25:42.962481
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import collections
import calendar
import datetime
from dateutil import relativedelta

from alembic import op

from ggrc_workflows.services import google_holidays


# revision identifiers, used by Alembic.
revision = 'ab78b910268'
down_revision = 'ab76b910268'

ANNUALLY_SQL = (
    'select w.id, t.id, t.relative_start_day, t.relative_start_month, '
    't.relative_end_day, t.relative_end_month, '
    'max(COALESCE(ct.start_date, CURDATE())) '
    'from workflows as w '
    'join task_groups as tg on tg.workflow_id = w.id '
    'join task_group_tasks as t on t.task_group_id = tg.id '
    'left join cycle_task_group_object_tasks as ct '
    'on ct.task_group_task_id = t.id '
    'where w.frequency = "annually" group by 1,2;'
)

UPDATE_TASKS_SQL = (
    "update task_group_tasks "
    "set start_date='{start_date}', "
    "end_date='{end_date}' "
    "where id in ({ids})"
)

UPDATE_WF_SQL = (
    "update workflows "
    "set repeat_multiplier='{repeat_multiplier}', "
    "next_cycle_start_date='{next_cycle_start_date}' "
    "where id = {id}"
)

YEAR = 2016


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  # pylint: disable=too-many-locals
  connection = op.get_bind()
  annually_tasks = connection.execute(ANNUALLY_SQL)

  tg_dates_dict = {}
  tg_wf = collections.defaultdict(set)
  ctg_wf = collections.defaultdict(set)

  for (
          wf,
          tgt,
          start_day,
          start_month,
          end_day,
          end_month,
          last_task_start_date) in annually_tasks:

    if not (start_day and end_day and start_month and end_month):
      continue
    tg_wf[wf].add(tgt)
    ctg_wf[wf].add(last_task_start_date)
    tg_dates_dict[tgt] = (start_day, start_month, end_day, end_month)

  today = datetime.date.today()
  group_days = collections.defaultdict(set)
  for wf, task_ids in tg_wf.iteritems():
    start_dates = []
    for task_id in task_ids:
      start_day, start_month, end_day, end_month = tg_dates_dict[task_id]
      _, max_start_day = calendar.monthrange(YEAR, start_month)
      _, max_end_day = calendar.monthrange(YEAR, end_month)
      start_date = datetime.date(YEAR,
                                 start_month,
                                 min(start_day, max_start_day))
      end_date = datetime.date(YEAR,
                               end_month,
                               min(end_day, max_end_day))
      while end_date < start_date:
        end_date += relativedelta.relativedelta(end_date, months=12)
      start_dates.append(start_date)
      group_days[(start_date, end_date)].add(task_id)
    startup_next_cycle_start_date = min(start_dates)
    next_cycle_start_date = startup_next_cycle_start_date
    repeat_multiplier = 0
    holidays = google_holidays.GoogleHolidays()
    # today required for cases there workflow hadn't started yet
    last_cycle_started_date = max([min(ctg_wf[wf]), today])
    while next_cycle_start_date <= last_cycle_started_date:
      repeat_multiplier += 1
      next_cycle_start_date = (
          startup_next_cycle_start_date + relativedelta.relativedelta(
              startup_next_cycle_start_date,
              months=repeat_multiplier * 12))
      while (next_cycle_start_date.isoweekday() > 5 or
             next_cycle_start_date in holidays):
        next_cycle_start_date -= relativedelta.relativedelta(days=1)
    op.execute(
        UPDATE_WF_SQL.format(repeat_multiplier=repeat_multiplier,
                             next_cycle_start_date=next_cycle_start_date,
                             id=wf)
    )
  for days, task_ids in group_days.iteritems():
    start_date, end_date = days
    op.execute(
        UPDATE_TASKS_SQL.format(start_date=start_date,
                                end_date=end_date,
                                ids=", ".join(str(i) for i in task_ids))
    )


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  pass

from datetime import datetime, timedelta
from typing import Optional

from tt.models import PRIORITY_REVERSE, Task


def filter_tasks(
    tasks: list[Task],
    project: Optional[str] = None,
    priority: Optional[str] = None,
    due: Optional[str] = None,
    tag: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[Task]:
    result = tasks

    if project:
        project_lower = project.lower()
        result = [t for t in result if t.project_name.lower() == project_lower]

    if priority:
        prio_val = PRIORITY_REVERSE.get(priority.lower())
        if prio_val is not None:
            result = [t for t in result if t.priority == prio_val]

    if due:
        result = _filter_by_due(result, due.lower())

    if tag:
        tag_lower = tag.lower()
        result = [t for t in result if any(tg.lower() == tag_lower for tg in t.tags)]

    if limit:
        result = result[:limit]

    return result


def _filter_by_due(tasks: list[Task], due_filter: str) -> list[Task]:
    now = datetime.now().astimezone()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)

    def local_date(t: Task):
        return t.due_date.astimezone().date() if t.due_date else None

    if due_filter == "today":
        return [t for t in tasks if local_date(t) == today.date()]
    elif due_filter == "tomorrow":
        return [t for t in tasks if local_date(t) == tomorrow.date()]
    elif due_filter == "week":
        return [t for t in tasks if local_date(t) is not None and today.date() <= local_date(t) <= week_end.date()]
    elif due_filter == "overdue":
        return [t for t in tasks if local_date(t) is not None and local_date(t) < today.date()]
    return tasks

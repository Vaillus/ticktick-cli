import json
from datetime import datetime, timedelta

from tt.models import Task


def _format_due(due: datetime | None) -> str:
    if not due:
        return "no due date"
    now = datetime.now().astimezone()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    local_due = due.astimezone()
    if local_due.date() == today.date():
        return "today"
    if local_due.date() == tomorrow.date():
        return "tomorrow"
    return local_due.strftime("%Y-%m-%d")


def format_compact(tasks: list[Task]) -> str:
    if not tasks:
        return "No tasks."
    lines = []
    for t in tasks:
        due = f", due: {_format_due(t.due_date)}" if t.due_date else ""
        project = f", {t.project_name}" if t.project_name else ""
        prio = f"[{t.priority_label}]"
        lines.append(f"[{t.short_id}] {prio:6s} {t.title}  ({project.lstrip(', ')}{due})")
    return "\n".join(lines)


def format_verbose(tasks: list[Task]) -> str:
    if not tasks:
        return "No tasks."
    blocks = []
    for t in tasks:
        lines = [
            f"ID:       {t.id} ({t.short_id})",
            f"Title:    {t.title}",
            f"Project:  {t.project_name or '(none)'}",
            f"Priority: {t.priority_label}",
            f"Due:      {_format_due(t.due_date)}",
        ]
        if t.content:
            lines.append(f"Content:  {t.content}")
        if t.tags:
            lines.append(f"Tags:     {', '.join(t.tags)}")
        blocks.append("\n".join(lines))
    return "\n---\n".join(blocks)


def format_json(tasks: list[Task]) -> str:
    items = []
    for t in tasks:
        items.append({
            "id": t.id,
            "short_id": t.short_id,
            "title": t.title,
            "project": t.project_name,
            "priority": t.priority_label.lower(),
            "due": _format_due(t.due_date) if t.due_date else None,
            "tags": t.tags,
            "content": t.content or None,
        })
    return json.dumps(items, indent=2)

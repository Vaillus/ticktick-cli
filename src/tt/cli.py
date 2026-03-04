import sys

import click


class ErrorHandlingGroup(click.Group):
    def invoke(self, ctx):
        try:
            return super().invoke(ctx)
        except (SystemExit, KeyboardInterrupt, click.Abort, click.exceptions.Exit):
            raise
        except click.ClickException:
            raise
        except Exception as e:
            if ctx.params.get("debug"):
                raise
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


@click.group(cls=ErrorHandlingGroup)
@click.option("--debug", is_flag=True, hidden=True, help="Show full stack traces")
@click.pass_context
def cli(ctx, debug):
    """tt — TickTick CLI"""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug


@cli.command()
@click.option("--status", is_flag=True, help="Check if token is valid")
def auth(status):
    """Authenticate with TickTick (OAuth2)."""
    if status:
        from tt.api import TickTickClient

        client = TickTickClient()
        client.get_projects()
        click.echo("Authenticated")
        return

    from tt.auth import run_oauth_flow

    run_oauth_flow()


@cli.command()
def projects():
    """List all projects."""
    from tt.api import TickTickClient

    client = TickTickClient()
    for p in client.get_projects():
        click.echo(f"{p.id}  {p.name}")


@cli.command("list")
@click.option("--project", "-p", help="Filter by project name")
@click.option("--priority", type=click.Choice(["none", "low", "medium", "high"], case_sensitive=False))
@click.option("--due", type=click.Choice(["today", "tomorrow", "week", "overdue"], case_sensitive=False))
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--json", "as_json", is_flag=True, help="JSON output")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--limit", "-n", type=int, help="Max results")
def list_tasks(project, priority, due, tag, as_json, verbose, limit):
    """List active tasks."""
    from tt.api import TickTickClient
    from tt.filters import filter_tasks
    from tt.formatters import format_compact, format_json, format_verbose

    client = TickTickClient()
    tasks = client.get_all_tasks()
    tasks = filter_tasks(tasks, project=project, priority=priority, due=due, tag=tag, limit=limit)

    if as_json:
        click.echo(format_json(tasks))
    elif verbose:
        click.echo(format_verbose(tasks))
    else:
        click.echo(format_compact(tasks))


@cli.command()
@click.argument("title")
@click.option("--project", "-p", help="Project name")
@click.option("--priority", type=click.Choice(["none", "low", "medium", "high"], case_sensitive=False), default="none")
@click.option("--due", help="Due date: today, tomorrow, or YYYY-MM-DD")
@click.option("--tag", "-t", multiple=True, help="Tag (repeatable)")
def add(title, project, priority, due, tag):
    """Add a new task."""
    from tt.api import TickTickClient
    from tt.formatters import format_compact
    from tt.models import PRIORITY_REVERSE

    client = TickTickClient()
    project_id = None
    if project:
        projects = client.get_projects()
        match = [p for p in projects if p.name.lower() == project.lower()]
        if not match:
            raise click.ClickException(f"Project not found: {project}")
        project_id = match[0].id

    task = client.create_task(
        title=title,
        project_id=project_id,
        priority=PRIORITY_REVERSE.get(priority.lower(), 0) if priority else 0,
        due_date=_parse_due(due),
        tags=list(tag) if tag else None,
    )
    click.echo(format_compact([task]))


@cli.command()
@click.argument("task_id")
def done(task_id):
    """Mark a task as complete."""
    from tt.api import TickTickClient

    client = TickTickClient()
    task = client.resolve_task(task_id)
    client.complete_task(task.project_id, task.id)
    click.echo(f"Completed: {task.title}")


@cli.command()
@click.argument("task_id")
@click.option("--title", help="New title")
@click.option("--priority", type=click.Choice(["none", "low", "medium", "high"], case_sensitive=False))
@click.option("--due", help="New due date: today, tomorrow, or YYYY-MM-DD")
def update(task_id, title, priority, due):
    """Update a task."""
    from tt.api import TickTickClient
    from tt.formatters import format_compact
    from tt.models import PRIORITY_REVERSE

    client = TickTickClient()
    task = client.resolve_task(task_id)

    updates = {}
    if title:
        updates["title"] = title
    if priority:
        updates["priority"] = PRIORITY_REVERSE.get(priority.lower(), 0)
    if due:
        updates["dueDate"] = _parse_due(due)

    if not updates:
        raise click.ClickException("Nothing to update. Use --title, --priority, or --due.")

    updated = client.update_task(task.id, task.project_id, updates)
    click.echo(format_compact([updated]))


@cli.command()
@click.argument("task_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def delete(task_id, force):
    """Delete a task."""
    from tt.api import TickTickClient

    client = TickTickClient()
    task = client.resolve_task(task_id)

    if not force:
        click.confirm(f"Delete '{task.title}'?", abort=True)

    client.delete_task(task.project_id, task.id)
    click.echo(f"Deleted: {task.title}")


@cli.command()
@click.argument("keyword")
@click.option("--project", "-p", help="Scope search to project")
def search(keyword, project):
    """Search tasks by keyword."""
    from tt.api import TickTickClient
    from tt.formatters import format_compact

    client = TickTickClient()
    tasks = client.get_all_tasks()

    keyword_lower = keyword.lower()
    results = [
        t for t in tasks
        if keyword_lower in t.title.lower() or keyword_lower in t.content.lower()
    ]

    if project:
        results = [t for t in results if t.project_name.lower() == project.lower()]

    if not results:
        click.echo("No tasks found.")
        return

    click.echo(format_compact(results))


@cli.command()
def tags():
    """List all tags used across tasks."""
    from tt.api import TickTickClient

    client = TickTickClient()
    tasks = client.get_all_tasks()
    all_tags: set[str] = set()
    for t in tasks:
        all_tags.update(t.tags)

    if not all_tags:
        click.echo("No tags found.")
        return

    for tag in sorted(all_tags):
        click.echo(tag)


def _parse_due(due_str: str | None) -> str | None:
    if not due_str:
        return None

    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if due_str.lower() == "today":
        dt = today
    elif due_str.lower() == "tomorrow":
        dt = today + timedelta(days=1)
    else:
        try:
            dt = datetime.strptime(due_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            raise click.ClickException(f"Invalid date: {due_str}. Use 'today', 'tomorrow', or YYYY-MM-DD.")
        return due_str + "T00:00:00+0000"
    return dt.strftime("%Y-%m-%dT%H:%M:%S+0000")

# tt — TickTick CLI

A minimal command-line interface for [TickTick](https://ticktick.com).

## Installation

Requires [uv](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/hugovaillaud/tt
cd tt
uv run python -m tt --help
```

Or install the `tt` command globally:

```bash
uv tool install .
```

## Authentication

See [AUTHENTICATION.md](AUTHENTICATION.md) for setup instructions (OAuth2 app creation required).

```bash
tt auth           # OAuth2 flow (opens browser)
tt auth --status  # Check token validity
```

For `tt completed` (uses TickTick's private API):

```bash
tt auth --cookie  # Save session credentials
```

Credentials are stored in `~/.config/tt/.env`.

## Commands

```
tt list                      List active tasks
tt add TITLE                 Add a task
tt done TASK_ID              Mark a task complete
tt update TASK_ID            Update a task
tt delete TASK_ID            Delete a task
tt search KEYWORD            Search tasks by keyword
tt projects                  List projects
tt tags                      List tags
tt completed                 List completed tasks
```

### Filters for `tt list`

```bash
tt list --project Work
tt list --priority high
tt list --due today
tt list --tag focus
tt list -n 10
```

### Options for `tt add`

```bash
tt add "Buy milk" --project Errands --due today --priority low --tag quick
```

### Options for `tt completed`

```bash
tt completed                  # Today
tt completed --due yesterday
tt completed --from 2025-01-01 --to 2025-01-31
```

### Output formats

All listing commands support `--verbose` / `-v` and `--json`.

## Running without installing

```bash
uv run python -m tt list
```

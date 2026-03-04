from typing import Any, Optional

import requests

from tt.config import (
    get_access_token,
    get_client_credentials,
    get_refresh_token,
    save_tokens,
)
from tt.models import Project, Task

BASE_URL = "https://api.ticktick.com/open/v1"


class TickTickClient:
    def __init__(self):
        self._access_token = get_access_token()
        self._refreshed = False

    def _request(self, method: str, endpoint: str, json: Any = None) -> Any:
        url = f"{BASE_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        resp = requests.request(method, url, headers=headers, json=json)

        if resp.status_code == 401 and not self._refreshed:
            self._refresh()
            headers["Authorization"] = f"Bearer {self._access_token}"
            resp = requests.request(method, url, headers=headers, json=json)

        resp.raise_for_status()

        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def _refresh(self) -> None:
        from tt.auth import refresh_access_token

        client_id, client_secret = get_client_credentials()
        refresh_token = get_refresh_token()
        token_data = refresh_access_token(refresh_token, client_id, client_secret)
        self._access_token = token_data["access_token"]
        new_refresh = token_data.get("refresh_token", refresh_token)
        save_tokens(self._access_token, new_refresh)
        self._refreshed = True

    def get_projects(self) -> list[Project]:
        data = self._request("GET", "/project")
        return [Project.from_api(p) for p in data]

    def get_project_tasks(self, project_id: str, project_name: str = "") -> list[Task]:
        data = self._request("GET", f"/project/{project_id}/data")
        tasks_data = data.get("tasks", []) or []
        return [Task.from_api(t, project_name=project_name) for t in tasks_data]

    def get_inbox_id(self) -> str | None:
        from tt.config import get_inbox_id as cached_id, save_inbox_id

        cached = cached_id()
        if cached:
            return cached
        try:
            data = self._request("GET", "/user")
            inbox_id = (data or {}).get("inboxId")
            if inbox_id:
                save_inbox_id(inbox_id)
                return inbox_id
        except Exception:
            pass
        # Fallback: fetch inbox tasks via the "inbox" alias and read the real ID
        try:
            data = self._request("GET", "/project/inbox/data")
            tasks = (data or {}).get("tasks") or []
            if tasks:
                inbox_id = tasks[0].get("projectId")
                if inbox_id:
                    save_inbox_id(inbox_id)
                    return inbox_id
        except Exception:
            pass
        return None

    def get_all_tasks(self) -> list[Task]:
        projects = self.get_projects()
        all_tasks: list[Task] = []
        inbox_id = self.get_inbox_id()
        if inbox_id:
            all_tasks.extend(self.get_project_tasks(inbox_id, "Inbox"))
        for p in projects:
            all_tasks.extend(self.get_project_tasks(p.id, p.name))
        return all_tasks

    def resolve_task(self, short_or_full_id: str) -> Task:
        all_tasks = self.get_all_tasks()
        query = short_or_full_id.lower()
        matches = [t for t in all_tasks if t.id.lower().startswith(query)]
        if len(matches) == 0:
            raise ValueError(f"No task found matching '{short_or_full_id}'")
        if len(matches) > 1:
            ids = ", ".join(t.short_id for t in matches)
            raise ValueError(f"Ambiguous ID '{short_or_full_id}' matches: {ids}")
        return matches[0]

    def create_task(
        self,
        title: str,
        project_id: Optional[str] = None,
        priority: int = 0,
        due_date: Optional[str] = None,
        tags: list[str] | None = None,
    ) -> Task:
        payload: dict[str, Any] = {"title": title, "priority": priority}
        if project_id:
            payload["projectId"] = project_id
        if due_date:
            payload["dueDate"] = due_date
        if tags:
            payload["tags"] = tags
        data = self._request("POST", "/task", json=payload)
        return Task.from_api(data)

    def update_task(self, task_id: str, project_id: str, updates: dict[str, Any]) -> Task:
        payload = {"id": task_id, "projectId": project_id, **updates}
        data = self._request("POST", f"/task/{task_id}", json=payload)
        return Task.from_api(data)

    def complete_task(self, project_id: str, task_id: str) -> None:
        self._request("POST", f"/project/{project_id}/task/{task_id}/complete")

    def delete_task(self, project_id: str, task_id: str) -> None:
        self._request("DELETE", f"/project/{project_id}/task/{task_id}")

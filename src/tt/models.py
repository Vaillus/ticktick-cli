from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

PRIORITY_MAP = {0: "---", 1: "LOW", 3: "MED", 5: "HIGH"}
PRIORITY_REVERSE = {"none": 0, "low": 1, "medium": 3, "med": 3, "high": 5}


@dataclass
class Project:
    id: str
    name: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Project":
        return cls(id=data["id"], name=data["name"])


@dataclass
class Task:
    id: str
    title: str
    project_id: str
    project_name: str = ""
    priority: int = 0
    due_date: Optional[datetime] = None
    content: str = ""
    tags: list[str] = field(default_factory=list)
    status: int = 0

    @property
    def short_id(self) -> str:
        return self.id[:6]

    @property
    def priority_label(self) -> str:
        return PRIORITY_MAP.get(self.priority, "---")

    @classmethod
    def from_api(cls, data: dict[str, Any], project_name: str = "") -> "Task":
        due = None
        due_str = data.get("dueDate")
        if due_str:
            try:
                due = datetime.fromisoformat(due_str.replace("+0000", "+00:00"))
            except ValueError:
                pass
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            project_id=data.get("projectId", ""),
            project_name=project_name,
            priority=data.get("priority", 0),
            due_date=due,
            content=data.get("content", ""),
            tags=data.get("tags", []) or [],
            status=data.get("status", 0),
        )

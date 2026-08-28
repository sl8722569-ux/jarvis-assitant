"""Phase 1 task board — queued / running / done / failed / waiting / cancelled."""
from __future__ import annotations

from dataclasses import dataclass, field


STATUSES = (
    "QUEUED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "WAITING_FOR_CONFIRMATION",
    "CANCELLED",
)


@dataclass
class Task:
    id: int
    name: str
    status: str = "QUEUED"
    detail: str = ""


@dataclass
class TaskBoard:
    tasks: list[Task] = field(default_factory=list)
    paused: bool = False
    _n: int = 0
    pending: dict | None = None  # confirmation payload

    def add(self, name: str, status: str = "QUEUED") -> Task:
        self._n += 1
        t = Task(id=self._n, name=name, status=status)
        self.tasks.append(t)
        return t

    def get(self, n: int) -> Task | None:
        for t in self.tasks:
            if t.id == n:
                return t
        return None

    def cancel(self, n: int) -> str:
        t = self.get(n)
        if not t:
            return f"No task {n}."
        if t.status in ("COMPLETED", "CANCELLED"):
            return f"Task {n} is already {t.status}."
        t.status = "CANCELLED"
        t.detail = "Cancelled by user."
        if self.pending and self.pending.get("task_id") == n:
            self.pending = None
        return f"Cancelled task {n} ({t.name})."

    def cancel_all(self) -> str:
        n = 0
        for t in self.tasks:
            if t.status in ("QUEUED", "RUNNING", "WAITING_FOR_CONFIRMATION"):
                t.status = "CANCELLED"
                n += 1
        self.pending = None
        return f"Cancelled {n} task(s)."

    def report(self) -> str:
        if not self.tasks:
            return "No tasks. I am idle."
        lines = ["Task board:"]
        for t in self.tasks[-12:]:
            extra = f" — {t.detail}" if t.detail else ""
            lines.append(f"{t.id}. {t.name}  — {t.status}{extra}")
        if self.paused:
            lines.append("(paused)")
        return "\n".join(lines)

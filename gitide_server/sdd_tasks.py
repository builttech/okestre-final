"""Task syntax shared by the REST API and MCP tools."""
import re
from typing import Optional

TASK_FILE = ".documents/task/task.md"
SDD_TASK_CODE_FRAGMENT = r"TASK-(?:REQ-\d{2,6}|RF-\d{2,6}-\d{1,4}|QA-[A-Z0-9-]+)-\d{3}"
SDD_TASK_CODE_PATTERN = re.compile(rf"\b{SDD_TASK_CODE_FRAGMENT}\b", flags=re.IGNORECASE)
SDD_TASK_LINE_PATTERN = re.compile(rf"^({SDD_TASK_CODE_FRAGMENT})\s*:\s*-?\s*(.+)$", flags=re.IGNORECASE)


def parse_task_line(line: str, line_index: int) -> Optional[dict]:
    checkbox = re.match(r"^\-\s*\[([ xX])\]\s*(.*)", (line or "").strip())
    if not checkbox:
        return None
    task = SDD_TASK_LINE_PATTERN.match(checkbox.group(2).strip())
    if not task:
        return None
    code, title = task.group(1).upper(), task.group(2).strip()
    return {"id": line_index, "line_no": line_index + 1, "code": code,
            "title": title, "text": f"{code}: - {title}", "checked": checkbox.group(1).lower() == "x"}

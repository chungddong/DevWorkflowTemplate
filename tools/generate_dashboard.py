from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATUS_FILE = ROOT / "docs" / "data" / "project-status.yaml"
OUTPUT_FILE = ROOT / "docs" / "DASHBOARD.html"


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value in {"null", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    lines = text.splitlines()

    for index, raw_line in enumerate(lines):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]

        if line.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"List item without list parent: {raw_line}")

            item_text = line[2:]
            if ": " in item_text:
                key, value = item_text.split(": ", 1)
                item: dict[str, Any] = {key: parse_scalar(value)}
                parent.append(item)
                stack.append((indent, item))
            elif item_text.endswith(":"):
                item = {item_text[:-1]: {}}
                parent.append(item)
                stack.append((indent, item[item_text[:-1]]))
            else:
                parent.append(parse_scalar(item_text))
            continue

        if ":" not in line:
            raise ValueError(f"Unsupported YAML line: {raw_line}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        if raw_value:
            parent[key] = parse_scalar(raw_value)
            continue

        next_container: Any = {}
        for next_raw in lines[index + 1 :]:
            if not next_raw.strip() or next_raw.lstrip().startswith("#"):
                continue
            next_indent = len(next_raw) - len(next_raw.lstrip(" "))
            next_line = next_raw.strip()
            if next_indent > indent and next_line.startswith("- "):
                next_container = []
            break

        parent[key] = next_container
        stack.append((indent, next_container))

    return root


def escape(value: Any) -> str:
    return html.escape(str(value))


def status_label(status: str) -> str:
    labels = {
        "done": "완료",
        "in_progress": "진행 중",
        "todo": "예정",
        "active": "활성",
        "blocked": "차단",
    }
    return labels.get(status, status)


def priority_label(priority: str) -> str:
    labels = {
        "high": "높음",
        "medium": "보통",
        "low": "낮음",
    }
    return labels.get(priority, priority)


def css_class(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "-", value)


def render_badge(status: str) -> str:
    return f'<span class="badge badge-{css_class(status)}">{escape(status_label(status))}</span>'


def render_priority(priority: str) -> str:
    return f'<span class="priority priority-{css_class(priority)}">{escape(priority_label(priority))}</span>'


def count_tasks(milestones: list[dict[str, Any]]) -> tuple[int, int]:
    total = 0
    done = 0
    for milestone in milestones:
        for task in milestone.get("tasks", []):
            total += 1
            if task.get("status") == "done":
                done += 1
    return done, total


def milestone_progress(milestone: dict[str, Any]) -> tuple[int, int, int]:
    tasks = milestone.get("tasks", [])
    total = len(tasks)
    done = sum(1 for task in tasks if task.get("status") == "done")
    percent = round(done / total * 100) if total else 0
    return done, total, percent


def render_goal_cards(goals: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"""
        <article class="goal-card">
          <div class="card-kicker">{escape(goal.get("id", ""))}</div>
          <h3>{escape(goal.get("title", ""))}</h3>
          <p>{escape(goal.get("description", ""))}</p>
          {render_badge(goal.get("status", ""))}
        </article>
        """
        for goal in goals
    )


def render_milestones(milestones: list[dict[str, Any]]) -> str:
    cards = []
    for milestone in milestones:
        done, total, percent = milestone_progress(milestone)
        tasks = "\n".join(
            f"""
            <li class="task task-{css_class(task.get("status", ""))}">
              <span class="task-marker"></span>
              <span>{escape(task.get("title", ""))}</span>
              <em>{escape(status_label(task.get("status", "")))}</em>
            </li>
            """
            for task in milestone.get("tasks", [])
        )
        cards.append(
            f"""
            <article class="milestone-card">
              <header>
                <div>
                  <div class="card-kicker">{escape(milestone.get("id", ""))}</div>
                  <h3>{escape(milestone.get("title", ""))}</h3>
                </div>
                {render_badge(milestone.get("status", ""))}
              </header>
              <p>{escape(milestone.get("objective", ""))}</p>
              <div class="progress-row">
                <div class="progress-track"><span style="width: {percent}%"></span></div>
                <strong>{percent}%</strong>
              </div>
              <div class="task-count">{done}/{total} 작업 완료</div>
              <ul class="task-list">{tasks}</ul>
            </article>
            """
        )
    return "\n".join(cards)


def render_todos(todos: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"""
        <tr>
          <td>{escape(todo.get("id", ""))}</td>
          <td class="todo-title">{escape(todo.get("title", ""))}</td>
          <td>{render_badge(todo.get("status", ""))}</td>
          <td>{render_priority(todo.get("priority", ""))}</td>
        </tr>
        """
        for todo in todos
    )


def render_links(links: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"""
        <a class="doc-link" href="{escape(link.get("path", ""))}">
          <span>{escape(link.get("title", ""))}</span>
          <small>{escape(link.get("path", ""))}</small>
        </a>
        """
        for link in links
    )


def render_dashboard(data: dict[str, Any]) -> str:
    project = data["project"]
    goals = data.get("goals", [])
    milestones = data.get("milestones", [])
    todos = data.get("todos", [])
    links = data.get("links", [])
    done_tasks, total_tasks = count_tasks(milestones)
    progress = round((done_tasks / total_tasks) * 100) if total_tasks else 0
    active_todos = [todo for todo in todos if todo.get("status") != "done"]
    done_todos = [todo for todo in todos if todo.get("status") == "done"]
    high_todos = [todo for todo in active_todos if todo.get("priority") == "high"]

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(project["name"])} 대시보드</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f3f5f8;
      --panel: #ffffff;
      --panel-soft: #f8fafc;
      --text: #16202f;
      --muted: #687386;
      --line: #d9e1ec;
      --blue: #2563a8;
      --teal: #087f8c;
      --green: #217a55;
      --amber: #a15c00;
      --red: #b42318;
      --gray: #667085;
      --shadow: 0 18px 46px rgba(22, 32, 47, 0.10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        linear-gradient(180deg, #eaf1f8 0, rgba(234, 241, 248, 0) 360px),
        var(--bg);
      color: var(--text);
      font-family: "Segoe UI", "Malgun Gothic", Arial, sans-serif;
      line-height: 1.55;
    }}
    main {{
      width: min(1240px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 48px;
    }}
    h1, h2, h3, p {{ margin-top: 0; }}
    h1 {{ margin-bottom: 10px; font-size: 34px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 20px; }}
    h3 {{ margin-bottom: 8px; font-size: 17px; }}
    .hero {{
      display: grid;
      grid-template-columns: 1.5fr 0.8fr;
      gap: 18px;
      align-items: stretch;
      margin-bottom: 18px;
    }}
    .hero-panel, .progress-panel, .metric, .tab-panel, .goal-card, .milestone-card {{
      background: rgba(255, 255, 255, 0.92);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }}
    .hero-panel {{
      padding: 28px;
    }}
    .hero-panel p {{
      max-width: 760px;
      margin-bottom: 18px;
      color: var(--muted);
      font-size: 16px;
    }}
    .phase {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}
    .phase strong {{
      color: var(--muted);
      font-size: 14px;
    }}
    .progress-panel {{
      display: grid;
      place-items: center;
      padding: 22px;
    }}
    .donut {{
      width: 176px;
      aspect-ratio: 1;
      display: grid;
      place-items: center;
      border-radius: 50%;
      background: conic-gradient(var(--blue) {progress}%, #e3e9f2 0);
      position: relative;
    }}
    .donut::after {{
      content: "";
      width: 124px;
      aspect-ratio: 1;
      position: absolute;
      border-radius: 50%;
      background: var(--panel);
      box-shadow: inset 0 0 0 1px var(--line);
    }}
    .donut-value {{
      position: relative;
      z-index: 1;
      text-align: center;
    }}
    .donut-value strong {{
      display: block;
      font-size: 34px;
      line-height: 1;
    }}
    .donut-value span {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .metric {{
      padding: 16px;
      box-shadow: none;
    }}
    .metric small {{
      display: block;
      color: var(--muted);
      font-weight: 700;
      margin-bottom: 8px;
    }}
    .metric strong {{
      display: block;
      font-size: 28px;
      line-height: 1;
    }}
    .tabs {{
      display: grid;
      gap: 0;
    }}
    .tabs input {{ display: none; }}
    .tab-labels {{
      display: flex;
      gap: 8px;
      padding: 8px;
      background: #e8eef6;
      border: 1px solid var(--line);
      border-radius: 8px;
      margin-bottom: 12px;
      overflow-x: auto;
    }}
    .tab-labels label {{
      min-width: max-content;
      padding: 9px 13px;
      border-radius: 6px;
      color: var(--muted);
      cursor: pointer;
      font-weight: 700;
      font-size: 14px;
    }}
    #tab-overview:checked ~ .tab-labels label[for="tab-overview"],
    #tab-milestones:checked ~ .tab-labels label[for="tab-milestones"],
    #tab-todos:checked ~ .tab-labels label[for="tab-todos"],
    #tab-docs:checked ~ .tab-labels label[for="tab-docs"] {{
      background: var(--panel);
      color: var(--blue);
      box-shadow: 0 1px 3px rgba(22, 32, 47, 0.12);
    }}
    .tab-panel {{
      display: none;
      padding: 18px;
      box-shadow: none;
    }}
    #tab-overview:checked ~ .panels #panel-overview,
    #tab-milestones:checked ~ .panels #panel-milestones,
    #tab-todos:checked ~ .panels #panel-todos,
    #tab-docs:checked ~ .panels #panel-docs {{
      display: block;
    }}
    .goal-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    .goal-card, .milestone-card {{
      padding: 16px;
      box-shadow: none;
    }}
    .card-kicker {{
      color: var(--teal);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      margin-bottom: 6px;
    }}
    .goal-card p, .milestone-card p {{
      color: var(--muted);
      margin-bottom: 12px;
    }}
    .milestone-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .milestone-card header {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      margin-bottom: 12px;
    }}
    .progress-row {{
      display: grid;
      grid-template-columns: 1fr 48px;
      gap: 10px;
      align-items: center;
      margin-bottom: 6px;
    }}
    .progress-row strong {{
      text-align: right;
      color: var(--blue);
      font-size: 14px;
    }}
    .progress-track {{
      height: 9px;
      overflow: hidden;
      border-radius: 999px;
      background: #e3e9f2;
    }}
    .progress-track span {{
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--teal), var(--blue));
    }}
    .task-count {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 12px;
    }}
    .task-list {{
      margin: 0;
      padding: 0;
      list-style: none;
    }}
    .task {{
      display: grid;
      grid-template-columns: 14px 1fr auto;
      gap: 8px;
      align-items: center;
      padding: 7px 0;
      border-top: 1px solid #eef2f7;
    }}
    .task-marker {{
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--gray);
    }}
    .task-done .task-marker {{ background: var(--green); }}
    .task-in_progress .task-marker {{ background: var(--blue); }}
    .task-todo .task-marker {{ background: var(--gray); }}
    .task em {{
      color: var(--muted);
      font-size: 12px;
      font-style: normal;
      font-weight: 700;
    }}
    .task-done span:nth-child(2) {{
      color: var(--muted);
      text-decoration: line-through;
    }}
    .badge, .priority {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      border: 1px solid currentColor;
    }}
    .badge-done, .badge-active {{ color: var(--green); background: #edf8f2; }}
    .badge-in_progress {{ color: var(--blue); background: #eef5ff; }}
    .badge-todo {{ color: var(--gray); background: #f2f4f7; }}
    .badge-blocked {{ color: var(--amber); background: #fff7e6; }}
    .priority-high {{ color: var(--red); background: #fff1f0; }}
    .priority-medium {{ color: var(--amber); background: #fff7e6; }}
    .priority-low {{ color: var(--gray); background: #f2f4f7; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }}
    th, td {{
      padding: 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: middle;
    }}
    th {{
      background: var(--panel-soft);
      color: var(--muted);
      font-size: 13px;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    .todo-title {{ font-weight: 700; }}
    .doc-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .doc-link {{
      display: grid;
      gap: 4px;
      padding: 13px;
      color: var(--text);
      text-decoration: none;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-soft);
    }}
    .doc-link span {{ font-weight: 800; }}
    .doc-link small {{ color: var(--muted); overflow-wrap: anywhere; }}
    .notice {{
      margin-top: 16px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 900px) {{
      .hero, .metrics, .goal-grid, .milestone-grid, .doc-grid {{
        grid-template-columns: 1fr;
      }}
      h1 {{ font-size: 28px; }}
      .tab-panel {{ padding: 14px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="hero-panel">
        <h1>{escape(project["name"])}</h1>
        <p>{escape(project.get("summary", ""))}</p>
        <div class="phase">
          {render_badge(project.get("status", ""))}
          <strong>{escape(project.get("phase", ""))}</strong>
        </div>
      </div>
      <aside class="progress-panel">
        <div class="donut" aria-label="전체 진행률 {progress}%">
          <div class="donut-value">
            <strong>{progress}%</strong>
            <span>전체 진행률</span>
          </div>
        </div>
      </aside>
    </section>

    <section class="metrics">
      <div class="metric"><small>마일스톤 작업</small><strong>{done_tasks}/{total_tasks}</strong></div>
      <div class="metric"><small>프로젝트 목표</small><strong>{len(goals)}</strong></div>
      <div class="metric"><small>남은 TODO</small><strong>{len(active_todos)}</strong></div>
      <div class="metric"><small>높은 우선순위</small><strong>{len(high_todos)}</strong></div>
    </section>

    <section class="tabs">
      <input checked id="tab-overview" name="dashboard-tabs" type="radio">
      <input id="tab-milestones" name="dashboard-tabs" type="radio">
      <input id="tab-todos" name="dashboard-tabs" type="radio">
      <input id="tab-docs" name="dashboard-tabs" type="radio">
      <div class="tab-labels">
        <label for="tab-overview">개요</label>
        <label for="tab-milestones">마일스톤</label>
        <label for="tab-todos">TODO</label>
        <label for="tab-docs">문서</label>
      </div>
      <div class="panels">
        <div class="tab-panel" id="panel-overview">
          <h2>목표</h2>
          <div class="goal-grid">{render_goal_cards(goals)}</div>
        </div>
        <div class="tab-panel" id="panel-milestones">
          <h2>마일스톤 진행</h2>
          <div class="milestone-grid">{render_milestones(milestones)}</div>
        </div>
        <div class="tab-panel" id="panel-todos">
          <h2>TODO 현황</h2>
          <table>
            <thead><tr><th>ID</th><th>작업</th><th>상태</th><th>우선순위</th></tr></thead>
            <tbody>{render_todos(active_todos + done_todos)}</tbody>
          </table>
        </div>
        <div class="tab-panel" id="panel-docs">
          <h2>주요 문서</h2>
          <div class="doc-grid">{render_links(links)}</div>
        </div>
      </div>
    </section>

    <p class="notice">이 파일은 docs/data/project-status.yaml을 기반으로 자동 생성되었습니다. 직접 수정하지 말고 tools/generate_dashboard.py를 실행해 갱신하세요.</p>
  </main>
</body>
</html>
"""


def main() -> None:
    data = parse_simple_yaml(STATUS_FILE.read_text(encoding="utf-8"))
    OUTPUT_FILE.write_text(render_dashboard(data), encoding="utf-8")
    print(f"generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

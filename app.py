import json
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import streamlit as st


APP_TITLE = "Life OS"
DATA_DIR = Path(".lifeos_data")
DATA_FILE = DATA_DIR / "lifeos.json"


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def default_data():
    return {
        "notes": [],
        "tasks": [],
        "projects": [],
        "inbox": [],
        "files": [],
    }


def load_data():
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        return default_data()
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return default_data()


def save_data(data):
    DATA_DIR.mkdir(exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def init_state():
    if "lifeos" not in st.session_state:
        st.session_state.lifeos = load_data()


def add_item(collection, item):
    st.session_state.lifeos[collection].append(item)
    save_data(st.session_state.lifeos)


def remove_item(collection, index):
    del st.session_state.lifeos[collection][index]
    save_data(st.session_state.lifeos)


def page_header(title, subtitle=""):
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def sidebar():
    st.sidebar.title("🧠 Life OS")
    st.sidebar.caption("Your information → organized → actionable")

    pages = [
        "Command Center",
        "Inbox",
        "Projects",
        "Tasks",
        "Notes",
        "Files",
        "AI Workspace",
        "Settings",
    ]
    return st.sidebar.radio("Navigate", pages)


def command_center():
    data = st.session_state.lifeos
    page_header(
        "Command Center",
        "A single place to understand and organize everything you are working on.",
    )

    total_tasks = len(data["tasks"])
    open_tasks = sum(1 for x in data["tasks"] if not x.get("completed"))
    projects = len(data["projects"])
    notes = len(data["notes"])
    inbox = len(data["inbox"])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Open Tasks", open_tasks)
    c2.metric("Projects", projects)
    c3.metric("Notes", notes)
    c4.metric("Inbox", inbox)
    c5.metric("Total Tasks", total_tasks)

    st.divider()

    st.subheader("⚡ Quick Capture")
    with st.form("quick_capture"):
        text = st.text_area(
            "Drop anything here",
            placeholder="An idea, reminder, question, meeting note, task, plan...",
            height=100,
        )
        submitted = st.form_submit_button("Capture")
        if submitted and text.strip():
            add_item(
                "inbox",
                {
                    "text": text.strip(),
                    "created_at": now_text(),
                    "processed": False,
                },
            )
            st.success("Captured successfully.")
            st.rerun()

    st.subheader("Today's Focus")
    open_items = [x for x in data["tasks"] if not x.get("completed")]
    if not open_items:
        st.info("No open tasks yet. Capture something above or create a task.")
    else:
        for task in open_items[:10]:
            st.write(f"• **{task['title']}** — {task.get('priority', 'Normal')}")

    st.subheader("Recent Activity")
    activity = []
    for x in data["notes"]:
        activity.append(("Note", x.get("title", "Untitled"), x.get("created_at", "")))
    for x in data["projects"]:
        activity.append(("Project", x.get("name", "Untitled"), x.get("created_at", "")))
    for x in data["inbox"]:
        activity.append(("Inbox", x.get("text", "")[:60], x.get("created_at", "")))

    activity.sort(key=lambda x: x[2], reverse=True)
    if activity:
        st.dataframe(
            pd.DataFrame(activity[:10], columns=["Type", "Item", "Created"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No activity yet.")


def inbox_page():
    data = st.session_state.lifeos
    page_header(
        "Inbox",
        "The universal landing place for ideas, information and things you do not want to lose.",
    )

    with st.form("inbox_add"):
        text = st.text_area("Capture", height=120)
        submitted = st.form_submit_button("Add to Inbox")
        if submitted and text.strip():
            add_item(
                "inbox",
                {"text": text.strip(), "created_at": now_text(), "processed": False},
            )
            st.success("Saved successfully.")
            st.rerun()

    st.divider()

    for i, item in enumerate(data["inbox"]):
        with st.container(border=True):
            st.write(item["text"])
            st.caption(item.get("created_at", ""))
            a, b = st.columns(2)
            if not item.get("processed"):
                if a.button("Mark Processed", key=f"process_{i}"):
                    item["processed"] = True
                    save_data(data)
                    st.rerun()
            else:
                a.success("Processed")
            if b.button("Delete", key=f"delete_inbox_{i}"):
                remove_item("inbox", i)
                st.rerun()


def projects_page():
    data = st.session_state.lifeos
    page_header("Projects", "Organize larger goals into manageable workspaces.")

    with st.form("new_project"):
        name = st.text_input("Project name")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Create Project")
        if submitted and name.strip():
            add_item(
                "projects",
                {
                    "name": name.strip(),
                    "description": description.strip(),
                    "created_at": now_text(),
                    "status": "Active",
                },
            )
            st.success("Project created successfully.")
            st.rerun()

    st.divider()

    if not data["projects"]:
        st.info("No projects yet.")
        return

    for i, project in enumerate(data["projects"]):
        with st.container(border=True):
            st.subheader(project["name"])
            if project.get("description"):
                st.write(project["description"])
            st.caption(f"Created: {project.get('created_at', '')} • {project.get('status', 'Active')}")
            if st.button("Delete Project", key=f"delete_project_{i}"):
                remove_item("projects", i)
                st.rerun()


def tasks_page():
    data = st.session_state.lifeos
    page_header("Tasks", "Turn intentions into concrete actions.")

    project_names = ["None"] + [x["name"] for x in data["projects"]]

    with st.form("new_task"):
        title = st.text_input("Task")
        priority = st.selectbox("Priority", ["Low", "Normal", "High", "Urgent"])
        due = st.date_input("Due date", value=date.today())
        project = st.selectbox("Project", project_names)
        submitted = st.form_submit_button("Create Task")
        if submitted and title.strip():
            add_item(
                "tasks",
                {
                    "title": title.strip(),
                    "priority": priority,
                    "due": str(due),
                    "project": project,
                    "completed": False,
                    "created_at": now_text(),
                },
            )
            st.success("Task created successfully.")
            st.rerun()

    st.divider()

    if not data["tasks"]:
        st.info("No tasks yet.")
        return

    for i, task in enumerate(data["tasks"]):
        with st.container(border=True):
            c1, c2, c3 = st.columns([0.08, 0.72, 0.20])
            checked = c1.checkbox(
                "",
                value=task.get("completed", False),
                key=f"task_check_{i}",
            )
            if checked != task.get("completed", False):
                task["completed"] = checked
                save_data(data)
                st.rerun()

            label = task["title"]
            if task.get("completed"):
                label = f"~~{label}~~"
            c2.markdown(label)
            c2.caption(
                f"Priority: {task.get('priority', 'Normal')} | "
                f"Due: {task.get('due', '')} | "
                f"Project: {task.get('project', 'None')}"
            )
            if c3.button("Delete", key=f"delete_task_{i}"):
                remove_item("tasks", i)
                st.rerun()


def notes_page():
    data = st.session_state.lifeos
    page_header("Notes", "Store ideas, decisions, knowledge and working material.")

    with st.form("new_note"):
        title = st.text_input("Title")
        content = st.text_area("Note", height=220)
        tags = st.text_input("Tags", placeholder="work, idea, research")
        submitted = st.form_submit_button("Save Note")
        if submitted and (title.strip() or content.strip()):
            add_item(
                "notes",
                {
                    "title": title.strip() or "Untitled",
                    "content": content.strip(),
                    "tags": [x.strip() for x in tags.split(",") if x.strip()],
                    "created_at": now_text(),
                },
            )
            st.success("Note saved successfully.")
            st.rerun()

    st.divider()

    for i, note in enumerate(data["notes"]):
        with st.expander(note.get("title", "Untitled")):
            st.write(note.get("content", ""))
            if note.get("tags"):
                st.caption("Tags: " + ", ".join(note["tags"]))
            st.caption(note.get("created_at", ""))
            if st.button("Delete Note", key=f"delete_note_{i}"):
                remove_item("notes", i)
                st.rerun()


def files_page():
    data = st.session_state.lifeos
    page_header(
        "Files",
        "Upload documents and images. This first version records them safely for the Life OS pipeline.",
    )

    uploads = st.file_uploader(
        "Upload files",
        accept_multiple_files=True,
        type=[
            "pdf",
            "txt",
            "md",
            "csv",
            "xlsx",
            "docx",
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
    )

    if uploads:
        for uploaded in uploads:
            raw = uploaded.getvalue()
            exists = any(
                x.get("name") == uploaded.name and x.get("size") == len(raw)
                for x in data["files"]
            )
            if not exists:
                add_item(
                    "files",
                    {
                        "name": uploaded.name,
                        "size": len(raw),
                        "type": uploaded.type,
                        "created_at": now_text(),
                    },
                )
        st.success("File information saved successfully.")
        st.rerun()

    st.divider()

    if data["files"]:
        st.dataframe(
            pd.DataFrame(data["files"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No files uploaded yet.")


def ai_workspace():
    page_header(
        "AI Workspace",
        "The future AI layer of Life OS. The interface is ready for provider integrations.",
    )

    st.info(
        "Life OS is intentionally being built as an AI-agnostic platform. "
        "We can connect one or more AI providers later without redesigning the core data model."
    )

    command = st.text_area(
        "What do you want Life OS to do?",
        placeholder=(
            "Examples:\n"
            "• Organize my inbox\n"
            "• Turn this note into a project\n"
            "• Make a checklist from this document\n"
            "• Summarize my current projects\n"
            "• Find unfinished work"
        ),
        height=160,
    )

    if st.button("Run AI Command"):
        if command.strip():
            st.session_state["last_ai_command"] = command.strip()
            st.success(
                "Command captured. The AI execution layer will be connected in the next development stage."
            )
        else:
            st.warning("Enter a command first.")

    if st.session_state.get("last_ai_command"):
        st.caption("Last command")
        st.write(st.session_state["last_ai_command"])


def settings_page():
    page_header("Settings", "Core Life OS configuration.")

    st.subheader("Architecture")
    st.write("Storage mode: Local application data")
    st.write("AI mode: Provider-agnostic")
    st.write("Application: Life OS")

    st.divider()

    st.subheader("Data")
    if st.button("Create Fresh Empty Workspace"):
        st.session_state.lifeos = default_data()
        save_data(st.session_state.lifeos)
        st.success("Workspace reset successfully.")
        st.rerun()

    st.download_button(
        "Export Life OS Data",
        data=json.dumps(st.session_state.lifeos, ensure_ascii=False, indent=2),
        file_name="lifeos_backup.json",
        mime="application/json",
    )


def main():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_state()

    page = sidebar()

    if page == "Command Center":
        command_center()
    elif page == "Inbox":
        inbox_page()
    elif page == "Projects":
        projects_page()
    elif page == "Tasks":
        tasks_page()
    elif page == "Notes":
        notes_page()
    elif page == "Files":
        files_page()
    elif page == "AI Workspace":
        ai_workspace()
    elif page == "Settings":
        settings_page()


if __name__ == "__main__":
    main()

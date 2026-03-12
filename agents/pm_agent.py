from langchain_core.messages import HumanMessage
from state import ProjectState
from agents import llm
import json

def create_wbs(state: ProjectState) -> ProjectState:
    print("\n🟡 PM Agent: Creating Work Breakdown Structure...")

    # ← This line was missing — defines in_scope before using it in the prompt
    in_scope = "\n".join(f"- {item}" for item in state["sow"].get("in_scope", []))

    prompt = f"""
You are a Project Manager. Based on the SOW and architecture below, break the 
development into a list of small, ordered coding tasks for a developer.

SOW In-Scope Features:
{in_scope}

Architecture:
{state['architecture_schema']}

STRICT RULES:
- Every single feature listed in the SOW In-Scope MUST have at least one task
- Tasks must be ordered by dependency (DB first, then logic, then UI)
- The final task must ALWAYS be: "Build the complete Streamlit app.py with 
  ALL CRUD operations: Register, Login, View Tasks, Create Task, Update Task, 
  Delete Task with confirmation, and Reports"
- Keep between 6 to 8 tasks max

Respond ONLY with a valid JSON array of strings.
No explanation. No markdown. Just the raw JSON array.
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        tasks = json.loads(response.content.strip())
    except json.JSONDecodeError:
        import re
        match = re.search(r'\[.*\]', response.content, re.DOTALL)
        tasks = json.loads(match.group()) if match else ["Task 1: Build the full CRUD app in app.py"]

    print(f"✅ WBS Created: {len(tasks)} tasks")
    for i, t in enumerate(tasks):
        print(f"   {i+1}. {t}")

    return {**state, "wbs_tasks": tasks, "current_task_index": 0}
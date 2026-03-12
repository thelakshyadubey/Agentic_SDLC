from langchain_core.messages import HumanMessage
from state import ProjectState
from agents import llm
from tools.file_ops import write_file

def dev_agent(state: ProjectState) -> ProjectState:
    task_index = state["current_task_index"]
    current_task = state["wbs_tasks"][task_index]
    qa_feedback = state.get("qa_feedback", "")
    iteration = state.get("iteration_count", 0)

    print(f"\n🟢 Dev Agent: Working on Task {task_index + 1}/{len(state['wbs_tasks'])}")
    print(f"   Task: {current_task}")

    feedback_section = ""
    if qa_feedback:
        feedback_section = f"""
The QA Agent reviewed your previous code and found these issues:
{qa_feedback}

Fix ALL issues before resubmitting.
"""

    prompt = f"""
You are a Senior Python Developer. Your job is to write clean, working Python code.

Project Architecture:
{state['architecture_schema']}

Current Task:
{current_task}

{feedback_section}

STRICT RULES — follow every single one:
- Use Streamlit for the UI
- Use SQLite (via sqlite3 built-in module) for the database
- All code goes into a single file: app.py
- Write the COMPLETE file every time, not just the changed parts
- Do NOT use placeholder comments like "# add code here"
- The app must be fully functional and runnable with `streamlit run app.py`
- ALWAYS use st.session_state to track current page and logged-in user
- ALWAYS use st.sidebar.selectbox() for navigation, NEVER st.sidebar.button()
- NEVER reset page state on user input — typing in a text field must not change the page
- Initialize ALL session_state keys at the top of main() before anything else
- Use st.rerun() after login/logout/delete to refresh state cleanly
- Password fields must use type="password"
- Delete must show a confirmation step before actually deleting
- After login, show only logged-in menu: View Tasks, Create Task, Update Task, Delete Task, Reports, Logout
- Before login, show only: Register, Login
- CRITICAL: When using st.selectbox for item selection (e.g., selecting a task), ensure you safely extract the ID. Do NOT pass a descriptive string like "Task 1" into an `int()` casting function without parsing it correctly.

Respond with ONLY the raw Python code. No explanation. No markdown fences.
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    code = response.content.strip()

    # Strip markdown fences if LLM adds them anyway
    if code.startswith("```"):
        code = "\n".join(code.split("\n")[1:])
    if code.endswith("```"):
        code = "\n".join(code.split("\n")[:-1])

    write_file("app.py", code)
    print(f"✅ Code written to generated_workspace/app.py ({len(code)} chars)")

    return {
        **state,
        "code_files": {"app.py": code},
        "qa_feedback": "",
        "qa_passed": False,
        "iteration_count": iteration + 1
    }
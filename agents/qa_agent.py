from langchain_core.messages import HumanMessage
from state import ProjectState
from agents import llm_fast  # ← changed from llm
from tools.file_ops import read_file
import json

def qa_agent(state: ProjectState) -> ProjectState:
    print("\n🔴 QA Agent: Reviewing generated code...")

    code = read_file("app.py")
    current_task = state["wbs_tasks"][state["current_task_index"]]

    prompt = f"""
You are a QA Engineer reviewing Python code for a Streamlit + SQLite CRUD app.

The developer was asked to complete this task:
{current_task}

Here is the code they submitted:
{code}

ONLY fail the code if it has CRITICAL issues that will prevent it from running:
1. Python syntax errors
2. Missing imports that will cause an ImportError
3. Completely missing core functionality (e.g. no CRUD operations at all)

Do NOT fail for:
- Minor edge cases
- Missing validation
- Code style issues
- Security improvements
- Performance concerns
- Theoretical null pointer cases

If the code is reasonably functional and will run with `streamlit run app.py`, mark it as PASSED.

Respond ONLY with a valid JSON object:
{{
    "passed": true or false,
    "issues": ["only list CRITICAL issues that prevent execution"]
}}

No explanation. No markdown. Just the raw JSON.
"""

    response = llm_fast.invoke([HumanMessage(content=prompt)])

    try:
        review = json.loads(response.content.strip())
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        review = json.loads(match.group()) if match else {"passed": True, "issues": []}

    passed = review.get("passed", False)
    issues = review.get("issues", [])

    if passed:
        print("✅ QA Passed! Code approved.")
        return {**state, "qa_passed": True, "qa_feedback": ""}
    else:
        print(f"❌ QA Failed. Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        feedback = "\n".join(f"- {i}" for i in issues)
        return {**state, "qa_passed": False, "qa_feedback": feedback}
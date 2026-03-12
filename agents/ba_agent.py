from langchain_core.messages import HumanMessage
from state import ProjectState
from agents import llm
import json

def generate_sow(state: ProjectState) -> ProjectState:
    print("\n🔵 BA Agent: Generating Statement of Work...")

    prompt = f"""
You are a Business Analyst. Based on the problem statement below, generate a detailed 
Statement of Work (SOW) for a To-do application.

Problem Statement: {state['problem_statement']}

Respond ONLY with a valid JSON object in this exact format:
{{
    "in_scope": [
        "list of features that WILL be built"
    ],
    "out_scope": [
        "list of features that will NOT be built"
    ]
}}

No explanation. No markdown. Just the raw JSON.
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        sow = json.loads(response.content.strip())
    except json.JSONDecodeError:
        # Fallback if LLM adds extra text
        import re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        sow = json.loads(match.group()) if match else {"in_scope": [], "out_scope": []}

    print(f"✅ SOW Generated:\n  In Scope: {sow.get('in_scope')}\n  Out Scope: {sow.get('out_scope')}")
    
    return {**state, "sow": sow}
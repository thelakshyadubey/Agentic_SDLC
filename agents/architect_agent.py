from langchain_core.messages import HumanMessage
from state import ProjectState
from agents import llm

def design_architecture(state: ProjectState) -> ProjectState:
    print("\n🟣 Architect Agent: Designing system architecture...")

    in_scope = "\n".join(f"- {item}" for item in state["sow"].get("in_scope", []))

    prompt = f"""
You are a Software Architect. Based on the SOW below, design the full technical 
architecture for a Python CRUD application using Streamlit (UI) and SQLite (database).

In-Scope Features:
{in_scope}

Your response must include:
1. The SQLite database schema (table name, columns, data types)
2. A list of all Python files needed and what each does
3. A Mermaid.js ER diagram of the database

Format your response exactly like this:

## Database Schema
<describe tables and columns clearly>

## File Structure
<list each file and its responsibility>

## Mermaid Diagram
```mermaid
erDiagram
    <your diagram here>
```
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    
    print("✅ Architecture designed.")
    print(response.content[:300] + "...")

    return {**state, "architecture_schema": response.content}
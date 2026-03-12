from typing import TypedDict, List, Dict, Optional

class ProjectState(TypedDict):
    # Phase 1: BA & Architect
    problem_statement: str
    sow: Dict[str, List[str]]          # {"in_scope": [...], "out_scope": [...]}
    architecture_schema: str           # Mermaid.js diagram + DB schema

    # Phase 2: PM & Sprints
    wbs_tasks: List[str]               # Sprint backlog
    current_task_index: int            # Which sprint task Dev is on

    # Phase 3: Dev/QA Loop
    code_files: Dict[str, str]         # {"app.py": "import streamlit..."}
    qa_feedback: str                   # Error logs if QA rejects
    qa_passed: bool                    # True = approved, False = loop back

    # Phase 4: UAT
    ready_for_uat: bool                # Pauses graph for human review
    iteration_count: int               # Tracks Dev/QA loop iterations


import json
import os
from datetime import datetime
from typing import TypedDict, Optional

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

load_dotenv() 



class IncidentState(TypedDict):
    incident_report: str        
    diagnosis: Optional[str]   
    proposed_fix: Optional[str] 
    confidence: Optional[float] 
    approved: Optional[bool]    
    execution_result: Optional[str]
    audit_trail: list          


LLM = ChatGroq(model="openai/gpt-oss-120b", temperature=0)


def log_step(state: IncidentState, step_name: str, detail: str) -> None:
    """Har node apna kaam audit_trail me likh deta hai — production me ye DB/Postgres me jayega."""
    state["audit_trail"].append({
        "step": step_name,
        "detail": detail,
        "timestamp": datetime.utcnow().isoformat(),
    })


# 2. Node: Diagnose — problem ka root cause samajhna

def diagnose_node(state: IncidentState) -> IncidentState:
    prompt = f"""You are an SRE diagnostic agent. Given this incident report, identify the
most likely root cause in 2-3 sentences. Be specific and technical.

Incident report:
{state['incident_report']}
y
Respond with ONLY the root cause analysis, nothing else."""

    response = LLM.invoke(prompt)
    diagnosis = response.content.strip()

    state["diagnosis"] = diagnosis
    log_step(state, "diagnose", diagnosis)
    print(f"\n DIAGNOSIS:\n{diagnosis}\n")
    return state



#. Node: Propose Fix 

def propose_fix_node(state: IncidentState) -> IncidentState:
    prompt = f"""You are an SRE remediation agent. Given this diagnosis, propose ONE specific
fix action. Also give a confidence score between 0.0 and 1.0 for how sure you are
this fix will resolve the issue.

Diagnosis:
{state['diagnosis']}

Respond in this exact format:
FIX: <one line description of the fix>
CONFIDENCE: <number between 0 and 1>"""

    response = LLM.invoke(prompt).content.strip()

    fix_line = next((l for l in response.split("\n") if l.startswith("FIX:")), "FIX: unknown")
    conf_line = next((l for l in response.split("\n") if l.startswith("CONFIDENCE:")), "CONFIDENCE: 0.5")

    fix = fix_line.replace("FIX:", "").strip()
    try:
        confidence = float(conf_line.replace("CONFIDENCE:", "").strip())
    except ValueError:
        confidence = 0.5

    state["proposed_fix"] = fix
    state["confidence"] = confidence
    log_step(state, "propose_fix", f"{fix} (confidence={confidence})")
    print(f" PROPOSED FIX: {fix}")
    print(f" CONFIDENCE: {confidence:.2f}\n")
    return state



#  Node: Human Approval Gate — safety-critical actions insaan se confirm karwana

def human_approval_node(state: IncidentState) -> IncidentState:
    if state["confidence"] < 0.6:
        print("  Low confidence fix — human review strongly recommended.")

    answer = input(f" Approve this fix? '{state['proposed_fix']}' (y/n): ").strip().lower()
    approved = answer == "y"

    state["approved"] = approved
    log_step(state, "human_approval", f"approved={approved}")
    return state



# 5. Node: Execute — mock action.
def execute_node(state: IncidentState) -> IncidentState:
    if state["approved"]:
        result = f" Executed fix: {state['proposed_fix']}"
    else:
        result = " Fix rejected by human reviewer. No action taken."

    state["execution_result"] = result
    log_step(state, "execute", result)
    print(f"\n{result}\n")
    return state


# 6. Graph wiring — LangGraph yaha decide karta hai flow kaise chalega

def build_graph():
    graph = StateGraph(IncidentState)

    graph.add_node("diagnose", diagnose_node)
    graph.add_node("propose_fix", propose_fix_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("execute", execute_node)

    graph.set_entry_point("diagnose")
    graph.add_edge("diagnose", "propose_fix")
    graph.add_edge("propose_fix", "human_approval")
    graph.add_edge("human_approval", "execute")
    graph.add_edge("execute", END)

    return graph.compile()


# . Run + persist audit log — ye "production discipline" dikhata hai

def save_log(state: IncidentState, path: str = "incident_log.json"):
    logs = []
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs.append({
        "incident_report": state["incident_report"],
        "diagnosis": state["diagnosis"],
        "proposed_fix": state["proposed_fix"],
        "confidence": state["confidence"],
        "approved": state["approved"],
        "execution_result": state["execution_result"],
        "audit_trail": state["audit_trail"],
    })

    with open(path, "w") as f:
        json.dump(logs, f, indent=2)

    print(f" Log saved to {path}")


if __name__ == "__main__":
    #  Fake incident (baad me isse real log/metric source se replace karna) 
    sample_incident = (
        "ALERT: payments-service p99 latency spiked to 4200ms (baseline 180ms). "
        "Error logs show: 'connection pool exhausted' repeated 340 times in last 5 minutes. "
        "DB CPU utilization at 92%. No recent deployments in last 2 hours."
    )

    initial_state: IncidentState = {
        "incident_report": sample_incident,
        "diagnosis": None,
        "proposed_fix": None,
        "confidence": None,
        "approved": None,
        "execution_result": None,
        "audit_trail": [],
    }

    app = build_graph()
    final_state = app.invoke(initial_state)
    save_log(final_state)
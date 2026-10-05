"""
Eval Script — Incident Response Agent
--------------------------------------
Ye script agent ko multiple sample incidents pe test karta hai BINA human
approval maange (auto-approve mode), taaki tu jaldi se dekh sake:
  - Agent kitna confident hai har incident pe
  - Diagnosis + fix quality kaisi hai across different scenarios

Ye "eval suite" hai jo README mein table ke roop mein dikhana hai —
recruiters isse dekh ke samajhte hain tune sirf ek demo nahi, testing
discipline bhi dikhaya hai.

Run:
    python eval.py
"""

import json
from incident_agent import (
    IncidentState,
    diagnose_node,
    propose_fix_node,
    log_step,
)


def run_eval(incidents_path: str = "sample_incidents.json"):
    with open(incidents_path, "r") as f:
        incidents = json.load(f)

    results = []

    for inc in incidents:
        print(f"\n{'='*60}")
        print(f"Running: {inc['id']}")
        print(f"{'='*60}")

        state: IncidentState = {
            "incident_report": inc["report"],
            "diagnosis": None,
            "proposed_fix": None,
            "confidence": None,
            "approved": None,
            "execution_result": None,
            "audit_trail": [],
        }

        # Diagnose + propose fix — human approval SKIP karte hain eval ke liye
        state = diagnose_node(state)
        state = propose_fix_node(state)

        results.append({
            "id": inc["id"],
            "diagnosis": state["diagnosis"],
            "proposed_fix": state["proposed_fix"],
            "confidence": state["confidence"],
        })

    # ---- Summary table print karo ----
    print(f"\n\n{'='*70}")
    print("EVAL SUMMARY")
    print(f"{'='*70}")
    print(f"{'ID':<10}{'Confidence':<15}{'Fix (truncated)'}")
    print("-" * 70)

    total_confidence = 0
    for r in results:
        conf = r["confidence"] or 0
        total_confidence += conf
        fix_preview = (r["proposed_fix"] or "")[:45]
        print(f"{r['id']:<10}{conf:<15.2f}{fix_preview}")

    avg_conf = total_confidence / len(results) if results else 0
    print("-" * 70)
    print(f"Average confidence across {len(results)} incidents: {avg_conf:.2f}")

    # Save full results for README / reporting
    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n📁 Full results saved to eval_results.json")


if __name__ == "__main__":
    run_eval()
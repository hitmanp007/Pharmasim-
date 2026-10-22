import json, os
from functools import lru_cache
from .scoring import build_result

PATH = os.path.join(os.path.dirname(__file__), "data", "clinical_cases.json")


@lru_cache(maxsize=1)
def _load():
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)


def list_scenarios():
    return _load()


def get_scenario(sid):
    return next((c for c in _load() if c["id"] == sid), None)


def evaluate(case, form):
    """Return (result, errors). form needs .get and .getlist (answers evaluated server-side)."""
    items, errors = [], []
    for q in case["questions"]:
        opts = {o["id"]: o for o in q["options"]}
        if q["type"] == "single":
            pick = form.get(q["id"], "")
            if pick not in opts:
                errors.append(f"Choose an answer: {q['prompt']}")
                continue
            o = opts[pick]
            items.append({"prompt": q["prompt"], "answer": o["text"], "earned": o["points"],
                          "max": max(x["points"] for x in q["options"]), "feedback": o["feedback"],
                          "critical": bool(o.get("critical"))})
        else:
            picks = set(form.getlist(q["id"]))
            if not picks or not picks <= set(opts):
                errors.append(f"Select at least one valid option: {q['prompt']}")
                continue
            right = {k for k, o in opts.items() if o["correct"]}
            hit, wrong, missed = picks & right, picks - right, right - picks
            fb = []
            if missed:
                fb.append("Missed safety checks: " + "; ".join(opts[k]["text"] for k in sorted(missed)) + ".")
            if wrong:
                fb.append("Not relevant here: " + "; ".join(opts[k]["text"] for k in sorted(wrong)) + ".")
            items.append({"prompt": q["prompt"], "answer": "; ".join(opts[k]["text"] for k in sorted(picks)),
                          "earned": len(hit) * q["points_each"], "max": len(right) * q["points_each"],
                          "feedback": " ".join(fb) or "All relevant checks identified.", "critical": bool(missed)})
    if errors:
        return None, errors
    return build_result(case, "clinical", items, case["explanation"]), []

BANDS = [(90, "Excellent: strong safety and accuracy habits."),
         (70, "Good: review the missed items below."),
         (50, "Developing: revisit the learning objective and retry."),
         (0, "Needs more practice: read the explanations, then retry.")]
RULES = "Points are fixed per question. There are no negative marks; unsafe choices score 0 and are flagged as safety-critical."


def percentage(earned, possible):
    return round(100 * earned / possible, 1) if possible else 0.0


def band(pct):
    return next(text for floor, text in BANDS if pct >= floor)


def build_result(scenario, module, items, explanation):
    earned = sum(i["earned"] for i in items)
    possible = sum(i["max"] for i in items)
    pct = percentage(earned, possible)
    return {"scenario_id": scenario["id"], "title": scenario["title"], "module": module, "items": items,
            "earned": earned, "possible": possible, "percent": pct, "feedback": band(pct),
            "explanation": explanation, "references": scenario.get("references", []), "rules": RULES}

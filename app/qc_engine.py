import json, math, os
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from .scoring import build_result

PATH = os.path.join(os.path.dirname(__file__), "data", "qc_scenarios.json")
UNITS = {"mass": {"kg": Decimal("1000000"), "g": Decimal("1000"), "mg": Decimal("1"), "ug": Decimal("0.001")},
         "volume": {"L": Decimal("1000"), "mL": Decimal("1"), "uL": Decimal("0.001")}}
OOS_NOTE = ("Out of specification: do not discard the result or retest only to get a pass. Report it and follow "
            "the documented OOS investigation and review procedure.")


def to_decimal(v):
    if v is None or isinstance(v, bool):
        raise ValueError("Missing or non-numeric value.")
    if isinstance(v, str):
        v = v.strip()
        if not v:
            raise ValueError("Missing value.")
    try:
        d = Decimal(str(v))
    except InvalidOperation:
        raise ValueError(f"Not a number: {v!r}")
    if not d.is_finite():
        raise ValueError("Value must be finite.")
    return d


def mean(values):
    vals = [to_decimal(v) for v in values]
    if not vals:
        raise ValueError("Cannot average an empty dataset.")
    return sum(vals) / len(vals)


def pct_deviation(value, reference):
    ref = to_decimal(reference)
    if ref == 0:
        raise ValueError("Reference value cannot be zero.")
    return (to_decimal(value) - ref) / ref * 100


def pct_label_claim(measured, label_claim):
    lc = to_decimal(label_claim)
    if lc <= 0:
        raise ValueError("Label claim must be positive.")
    return to_decimal(measured) / lc * 100


def convert(value, from_unit, to_unit):
    for table in UNITS.values():
        if from_unit in table and to_unit in table:
            return to_decimal(value) * table[from_unit] / table[to_unit]
    raise ValueError(f"Unsupported or incompatible units: {from_unit} -> {to_unit}")


def within_limits(value, low=None, high=None, inclusive=True):
    v = to_decimal(value)
    if low is None and high is None:
        raise ValueError("At least one limit is required.")
    lo_ok = low is None or (v >= to_decimal(low) if inclusive else v > to_decimal(low))
    hi_ok = high is None or (v <= to_decimal(high) if inclusive else v < to_decimal(high))
    return lo_ok and hi_ok


def validate_scenario(s):
    for k in ("id", "title", "data", "criteria", "questions"):
        if k not in s:
            raise ValueError(f"Scenario missing '{k}'.")
    if not s["data"]:
        raise ValueError("Scenario dataset is empty.")
    [to_decimal(v) for v in s["data"]]
    if s["criteria"].get("type") not in EVALUATORS:
        raise ValueError("Unknown evaluation type.")


def _weight_variation(s):
    c = s["criteria"]
    m = mean(s["data"])
    devs = [abs(pct_deviation(v, m)) for v in s["data"]]
    n_a = sum(d > Decimal(str(c["flag_pct"])) for d in devs)
    n_b = sum(d > Decimal(str(c["hard_pct"])) for d in devs)
    ok = n_b == 0 and n_a <= c["max_flagged"]
    return {"mean": m, "decision": "pass" if ok else "fail",
            "explanation": f"Mean = {m:.2f} {s['unit']}. Units deviating more than {c['flag_pct']}% from the batch mean: {n_a}; more than {c['hard_pct']}%: {n_b}. "
                           + ("Exercise criteria met." if ok else "Exercise criteria not met. " + OOS_NOTE)}


def _assay(s):
    c = s["criteria"]
    m = mean(s["data"])
    pct = pct_label_claim(m, c["label_claim"])
    ok = within_limits(pct, c["low"], c["high"])
    return {"mean": m, "pct_lc": pct, "decision": "pass" if ok else "fail",
            "explanation": f"Mean = {m:.2f} {s['unit']}; % label claim = {pct:.2f}%. Limits: {c['low']}-{c['high']}% (inclusive). "
                           + ("Within limits for this exercise." if ok else OOS_NOTE)}


def _dissolution_s1(s):
    c = s["criteria"]
    m = mean(s["data"])
    floor = Decimal(str(c["q"])) + Decimal(str(c["s1_margin"]))
    lowest = min(to_decimal(v) for v in s["data"])
    ok = lowest >= floor
    return {"mean": m, "decision": "pass" if ok else "fail",
            "explanation": f"Mean = {m:.2f}%. S1 rule for this exercise: every unit >= Q + {c['s1_margin']} = {floor}%. Lowest unit = {lowest}%. "
                           + ("Stage S1 met." if ok else "Stage S1 not met. Follow the next stage and investigation steps defined in the method and SOP; do not discard or selectively repeat results.")}


EVALUATORS = {"weight_variation": _weight_variation, "assay": _assay, "dissolution_s1": _dissolution_s1}


@lru_cache(maxsize=1)
def _load():
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)


def list_scenarios():
    return _load()


def get_scenario(sid):
    return next((c for c in _load() if c["id"] == sid), None)


def evaluate(s, form):
    validate_scenario(s)
    res = EVALUATORS[s["criteria"]["type"]](s)
    items, errors = [], []
    for q in s["questions"]:
        raw = (form.get(q["id"]) or "").strip()
        if not raw:
            errors.append(f"Answer required: {q['prompt']}")
            continue
        if q["type"] == "numeric":
            try:
                val = to_decimal(raw)
            except ValueError:
                errors.append(f"Enter a valid number: {q['prompt']}")
                continue
            exp = res[q["key"]]
            ok = abs(val - exp) <= Decimal(str(q["tolerance"]))
            items.append({"prompt": q["prompt"], "answer": raw, "earned": q["points"] if ok else 0, "max": q["points"],
                          "feedback": f"Correct value: {exp:.2f} {q.get('unit', '')} (tolerance ±{q['tolerance']}).", "critical": False})
        else:
            if raw not in {o["id"] for o in q["options"]}:
                errors.append(f"Choose a valid option: {q['prompt']}")
                continue
            ok = raw == res["decision"]
            label = {o["id"]: o["text"] for o in q["options"]}
            items.append({"prompt": q["prompt"], "answer": label[raw], "earned": q["points"] if ok else 0, "max": q["points"],
                          "feedback": ("Correct. " if ok else f"Expected: {label[res['decision']]}. ") + res["explanation"],
                          "critical": not ok})
    if errors:
        return None, errors
    return build_result(s, "qc", items, res["explanation"] + " Synthetic data: a simulated pass is never evidence for releasing a real batch."), []

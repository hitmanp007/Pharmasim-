from decimal import Decimal
import pytest
from app import qc_engine as q


def test_mean():
    assert q.mean([1, 2, 3, 4]) == Decimal("2.5")


@pytest.mark.parametrize("bad", [[], [1, None], [1, "x"], [float("nan")], [True]])
def test_mean_rejects_bad(bad):
    with pytest.raises(ValueError):
        q.mean(bad)


def test_pct_deviation_and_zero():
    assert q.pct_deviation(105, 100) == Decimal(5)
    with pytest.raises(ValueError):
        q.pct_deviation(5, 0)


def test_label_claim():
    assert q.pct_label_claim(475, 500) == Decimal(95)
    with pytest.raises(ValueError):
        q.pct_label_claim(1, 0)


def test_convert():
    assert q.convert(1, "g", "mg") == Decimal(1000)
    assert q.convert(500, "uL", "mL") == Decimal("0.5")
    with pytest.raises(ValueError):
        q.convert(1, "g", "mL")
    with pytest.raises(ValueError):
        q.convert(1, "stone", "g")


def test_limits_boundaries():
    assert q.within_limits(95.0, 95.0, 105.0)
    assert q.within_limits(105.0, 95.0, 105.0)
    assert not q.within_limits("94.99", 95.0, 105.0)
    assert not q.within_limits(95.0, 95.0, 105.0, inclusive=False)


def sc(kind, data, **crit):
    return {"id": "x", "title": "t", "unit": "mg", "data": data, "criteria": {"type": kind, **crit}, "questions": []}


def test_weight_boundary_exactly_5pct_is_not_flagged():
    r = q.EVALUATORS["weight_variation"](sc("weight_variation", [190, 210] + [200] * 8, flag_pct=5, hard_pct=10, max_flagged=0))
    assert r["decision"] == "pass"


def test_weight_fail_hard_limit():
    r = q.EVALUATORS["weight_variation"](sc("weight_variation", [150] + [200] * 9, flag_pct=5, hard_pct=10, max_flagged=2))
    assert r["decision"] == "fail" and "investigation" in r["explanation"]


def test_dissolution_s1_pass_and_fail():
    ok = sc("dissolution_s1", [85, 90, 91], q=80, s1_margin=5)
    bad = sc("dissolution_s1", [84, 90, 91], q=80, s1_margin=5)
    assert q.EVALUATORS["dissolution_s1"](ok)["decision"] == "pass"
    assert q.EVALUATORS["dissolution_s1"](bad)["decision"] == "fail"


def test_malformed_datasets():
    for bad in ({"id": "x"}, sc("assay", [], label_claim=1, low=1, high=2), sc("assay", [1, "a"]), sc("nope", [1])):
        with pytest.raises(ValueError):
            q.validate_scenario(bad)


def test_bundled_scenarios_valid_and_deterministic():
    for s in q.list_scenarios():
        q.validate_scenario(s)
        form = {qq["id"]: ("1" if qq["type"] == "numeric" else "pass") for qq in s["questions"]}
        assert q.evaluate(s, form)[0] == q.evaluate(s, form)[0]

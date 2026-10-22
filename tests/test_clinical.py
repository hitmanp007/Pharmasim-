from werkzeug.datastructures import MultiDict
from app import clinical_engine as c, scoring


def test_correct_allergy_answers_full_score():
    case = c.get_scenario("allergy-amoxicillin")
    r, err = c.evaluate(case, MultiDict([("q1", "b"), ("q2", "a"), ("q2", "b")]))
    assert not err and r["earned"] == r["possible"] == 9 and r["percent"] == 100.0


def test_unsafe_answer_flagged_zero():
    case = c.get_scenario("allergy-amoxicillin")
    r, _ = c.evaluate(case, MultiDict([("q1", "a"), ("q2", "a")]))
    assert r["items"][0]["earned"] == 0 and r["items"][0]["critical"]
    assert "Missed safety checks" in r["items"][1]["feedback"]
    assert r["items"][1]["earned"] == 2


def test_interaction_partial_credit():
    case = c.get_scenario("interaction-warfarin-nsaid")
    r, _ = c.evaluate(case, MultiDict([("q1", "d"), ("q2", "a"), ("q2", "d")]))
    assert r["items"][0]["earned"] == 1 and r["items"][1]["earned"] == 2


def test_missing_and_invalid_answers():
    case = c.get_scenario("duplication-nsaids")
    assert c.evaluate(case, MultiDict())[0] is None
    r, err = c.evaluate(case, MultiDict([("q1", "zzz"), ("q2", "a")]))
    assert r is None and len(err) == 1


def test_unknown_scenario_and_scoring():
    assert c.get_scenario("nope") is None
    assert scoring.percentage(0, 0) == 0.0 and scoring.percentage(1, 3) == 33.3


def test_every_case_has_references_and_faculty_flag():
    for case in c.list_scenarios():
        assert case["references"] and case["faculty_review"]

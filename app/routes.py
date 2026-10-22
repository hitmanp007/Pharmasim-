from flask import Blueprint, abort, render_template, request, session
from . import clinical_engine, models, qc_engine

bp = Blueprint("main", __name__)
MODULES = {"clinical": (clinical_engine, "Clinical Pharmacy Simulator"),
           "qc": (qc_engine, "Pharmaceutical QC Lab Simulator")}


def _mod(name):
    if name not in MODULES:
        abort(404)
    return MODULES[name]


@bp.route("/health")
def health():
    return {"status": "ok"}


@bp.route("/")
def index():
    return render_template("index.html", modules=MODULES)


@bp.route("/m/<module>")
def scenario_list(module):
    eng, label = _mod(module)
    return render_template("list.html", module=module, label=label, scenarios=eng.list_scenarios())


@bp.route("/m/<module>/<sid>", methods=["GET", "POST"])
def scenario(module, sid):
    eng, label = _mod(module)
    s = eng.get_scenario(sid)
    if s is None:
        abort(404)
    if request.method == "POST":
        try:
            result, errors = eng.evaluate(s, request.form)
        except ValueError as exc:
            result, errors = None, [str(exc)]
        if errors:
            return render_template("scenario.html", module=module, label=label, s=s, errors=errors), 400
        models.record_attempt(session["sid"], module, sid, result["earned"], result["possible"], result["percent"])
        return render_template("results.html", module=module, s=s, r=result)
    return render_template("scenario.html", module=module, label=label, s=s, errors=[])


@bp.route("/progress")
def progress():
    rows = models.history(session["sid"])
    avg = round(sum(r["percent"] for r in rows) / len(rows), 1) if rows else None
    return render_template("progress.html", rows=rows, avg=avg)


@bp.route("/about")
def about():
    return render_template("about.html")

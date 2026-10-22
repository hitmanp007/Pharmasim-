# PharmaSim

Lightweight educational simulator for pharmacy students: a **Clinical Pharmacy Simulator** and a **Pharmaceutical QC Lab Simulator**. Flask, SQLite, Bootstrap 5, Chart.js, deterministic Python scoring. No API keys.

**All cases are fictional and all lab data synthetic. Not clinical advice. A simulated pass is never evidence for releasing a real batch.** Clinical cases are flagged *requires faculty review* and must be validated by a qualified pharmacy educator against current labeling (DailyMed/FDA) before teaching use.

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py          # development mode, http://127.0.0.1:5000
```
The SQLite database is created automatically on startup (`instance/pharmasim.db`).

## Tests
```powershell
python -m pytest -q
```

## Configuration
| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Required in production. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `PHARMASIM_ENV` | `production` (default) or `development` |
| `DATABASE_PATH` | SQLite file path (use a persistent disk path on the host) |

Copy `.env.example` for reference; never commit real values.

## GitHub and deployment (Render)
```powershell
git init; git add .; git commit -m "PharmaSim"
git remote add origin https://github.com/<you>/pharmasim.git; git push -u origin main
```
On Render: New Web Service, connect the repo, build `pip install -r requirements.txt`, start `gunicorn 'app:create_app()'`, health check path `/health`. Set `SECRET_KEY`, and add a persistent disk mounted at `/var/data` with `DATABASE_PATH=/var/data/pharmasim.db`. **Without a persistent disk, SQLite data is erased on restart or redeploy.** The data layer uses plain SQL so it can move to PostgreSQL later. Verify by opening `/health` (expects `{"status":"ok"}`) and completing one scenario.

Troubleshooting: `RuntimeError: SECRET_KEY` means the variable is unset; 400 on submit usually means an expired session/CSRF token (reload the page); lost history after deploy means no persistent disk.

## Add a clinical case
Append an object to `app/data/clinical_cases.json` following an existing case (`patient`, `questions` with option `points`/`feedback`, `explanation`, `references`, `faculty_review: true`). Cite official labeling; omit any claim you cannot verify.

## Add a QC scenario
Append to `app/data/qc_scenarios.json` with explicit `unit`, `data`, `criteria` (with its own limits and `text`) and `questions`. Reuse an evaluator in `app/qc_engine.py` (`EVALUATORS`) or add one; never use a universal pass/fail threshold.

## Known limitations
Anonymous sessions only (no accounts); history is tied to the browser cookie.

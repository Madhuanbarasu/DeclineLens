# Deployment and Run Guide

## 0. Prerequisites
* Python 3.10+ (Windows, macOS or Linux)
* Exasol Personal (free): <https://docs.exasol.com/db/latest/get_started/exasol_personal.htm>

## 1. Get Exasol Personal running
Follow the official Exasol Personal instructions for your operating system:
<https://exasol.github.io/exasol-personal>. It can run locally on macOS, Linux and Windows, or in your own cloud account. On macOS/Linux the quick start is:

```bash
curl https://downloads.exasol.com/exasol-personal/installer.sh | sh
exasol install local
exasol connect          # then try: SELECT 1;
```

On Windows, use the Windows instructions on the Exasol Personal pages. Note the **host, port, user and password** of your deployment (the Exasol Launcher can show connection details; `exasol --help` lists its commands).

## 2. Install this project
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Point it at your database
```powershell
$env:EXASOL_DSN = "<host>:<port>"
$env:EXASOL_USER = "<user>"
$env:EXASOL_PASSWORD = "<password>"
```
(macOS/Linux: `export EXASOL_DSN=...` etc.) Exasol Personal normally uses a self-signed certificate, so certificate verification is off by default. Set `EXASOL_VERIFY_CERT=1` to turn it on.

## 4. Run
```powershell
python -m declinelens --backend exasol run --rows 200000
```
Expected: five timed stages and a line like `declined=~68,000  with a path to approval=~53,000  what-if evaluations=~14,000,000`.

```powershell
python -m declinelens --backend exasol explain            # sample customer letter
$env:BACKEND = "exasol"; streamlit run declinelens/app.py # dashboard at http://localhost:8501
python -m declinelens --backend exasol bench              # scale timings -> docs/BENCHMARK.md
pytest -q tests                                           # correctness tests (use DuckDB)
```

## 5. No database yet?
Everything also runs on a local DuckDB file with the same SQL:
```powershell
python -m declinelens --backend duckdb run --rows 200000
$env:BACKEND = "duckdb"; streamlit run declinelens/app.py
```

## Troubleshooting
* **Connection refused / timeout:** check host, port and that the database is started.
* **Authentication failed:** re-check user and password from your deployment.
* **Certificate errors:** leave `EXASOL_VERIFY_CERT` unset (default), or install a trusted certificate and set it to `1`.
* **A SQL error on Exasol:** open an issue with the message. All SQL lives in `sql/` and uses plain ANSI constructs (CROSS JOIN, ROW_NUMBER, LEAST/GREATEST).
* **Dashboard shows nothing:** run the `run` command first so the tables exist.

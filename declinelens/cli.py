import argparse
import time
from pathlib import Path

from declinelens import explain, pipeline
from declinelens.db import DB


def _open(a, read_only=False):
    return DB(a.backend, read_only=read_only)


def cmd_run(a):
    db = _open(a)
    pipeline.run(db, n=a.rows, seed=a.seed, cutoff=a.cutoff)
    db.close()


def cmd_explain(a):
    db = _open(a, read_only=(a.backend == "duckdb"))
    if a.app_id:
        app_id = a.app_id
    else:
        app_id = db.scalar("SELECT app_id FROM declinelens.recourse_best WHERE rn = 1 ORDER BY effort DESC, app_id LIMIT 1")
    print(explain.build_letter(explain.get_case(db, app_id)))
    db.close()


def cmd_bench(a):
    rows = []
    for n in a.sizes:
        db = DB(a.backend, path=":memory:" if a.backend == "duckdb" else None)
        t0 = time.perf_counter()
        s = pipeline.run(db, n=n, log=lambda *_: None)
        s["total_seconds"] = time.perf_counter() - t0
        rows.append(s)
        print(f"{n:>10,} applicants | {s['evaluations']:>14,} what-ifs | recourse step {s['recourse_seconds']:.2f}s")
        db.close()
    out = Path("docs/BENCHMARK.md")
    out.parent.mkdir(exist_ok=True)
    note = ("> These numbers come from the local DuckDB stand-in, NOT Exasol. Run "
            "`python -m declinelens --backend exasol bench` to regenerate this file on Exasol Personal."
            if a.backend == "duckdb" else "> Measured on Exasol Personal.")
    lines = [f"# Benchmark ({a.backend})", "", note, "",
             "| Applicants | Declined | What-if evaluations | Recourse step (s) | Whole pipeline incl. generation (s) |",
             "|---:|---:|---:|---:|---:|"]
    for s in rows:
        lines.append(f"| {s['applicants']:,} | {s['declined']:,} | {s['evaluations']:,} | "
                     f"{s['recourse_seconds']:.2f} | {s['total_seconds']:.1f} |")
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out}")


def main():
    ap = argparse.ArgumentParser(prog="declinelens")
    ap.add_argument("--backend", choices=["exasol", "duckdb"], default="exasol")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="generate data, load, score, explain, audit")
    r.add_argument("--rows", type=int, default=200_000)
    r.add_argument("--seed", type=int, default=42)
    r.add_argument("--cutoff", type=float, default=0.5)
    r.set_defaults(fn=cmd_run)
    e = sub.add_parser("explain", help="print the customer letter for one applicant")
    e.add_argument("app_id", nargs="?")
    e.set_defaults(fn=cmd_explain)
    b = sub.add_parser("bench", help="time the pipeline at several sizes")
    b.add_argument("--sizes", type=int, nargs="+", default=[100_000, 500_000, 1_000_000])
    b.set_defaults(fn=cmd_bench)
    a = ap.parse_args()
    a.fn(a)

"""End-to-end run: generate -> train -> load -> score -> reasons -> recourse -> audit."""
import math

import pandas as pd

from declinelens import data, model, plans


def run(db, n: int = 200_000, seed: int = 42, cutoff: float = 0.5, log=print) -> dict:
    stats = []

    def mark(stage, rows, secs):
        stats.append({"stage_name": stage, "row_count": float(rows), "elapsed_s": float(secs)})
        log(f"  {stage:<28} {rows:>12,.0f} rows  {secs:7.2f}s")

    log(f"DeclineLens run: {n:,} applicants on {db.backend}")
    df = data.generate_applicants(n, seed)
    coef = model.train(df)

    mark("schema", 0, db.run_script("01_schema.sql"))
    import time
    t0 = time.perf_counter()
    db.load_df(df, "applicants")
    db.load_df(model.coef_frame(coef), "credit_model")
    db.load_df(pd.DataFrame({"cutoff": [cutoff], "z_cut": [math.log(cutoff / (1 - cutoff))]}), "run_config")
    plan_df = plans.build_plans()
    db.load_df(plan_df, "recourse_plans")
    db.load_df(plans.reason_frame(), "reason_text")
    mark("load", n, time.perf_counter() - t0)

    mark("score + decide", n, db.run_script("02_score.sql"))
    n_declined = int(db.scalar("SELECT COUNT(*) FROM declinelens.declined"))
    mark("reason codes", n_declined, db.run_script("03_reasons.sql"))
    evals = n_declined * len(plan_df)
    mark("recourse search (what-ifs)", evals, db.run_script("04_recourse.sql"))
    mark("fairness audit", n, db.run_script("05_audit.sql"))

    helped = int(db.scalar("SELECT COUNT(DISTINCT app_id) FROM declinelens.recourse_best"))
    db.load_df(pd.DataFrame(stats), "run_stats")
    summary = {
        "applicants": n, "declined": n_declined, "approval_rate": 1 - n_declined / n,
        "plans": len(plan_df), "evaluations": evals,
        "with_recourse": helped, "stranded": n_declined - helped,
        "recourse_seconds": stats[-2]["elapsed_s"],
    }
    log(f"  declined={n_declined:,}  with a path to approval={helped:,}  "
        f"stranded={n_declined - helped:,}  what-if evaluations={evals:,}")
    return summary

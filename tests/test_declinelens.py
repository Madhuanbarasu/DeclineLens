"""Correctness tests. The SQL engine is checked against an independent pure-Python reference,
including a brute-force proof that the recommended recourse really is the cheapest one."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from declinelens import model, pipeline, plans, scoring  # noqa: E402
from declinelens.db import DB  # noqa: E402


@pytest.fixture(scope="module")
def env():
    db = DB("duckdb", path=":memory:")
    pipeline.run(db, n=4000, seed=11, log=lambda *_: None)
    coef = db.query("SELECT * FROM declinelens.credit_model").iloc[0].to_dict()
    z_cut = float(db.scalar("SELECT z_cut FROM declinelens.run_config"))
    return db, coef, z_cut


def test_sql_scores_match_python(env):
    db, coef, _ = env
    df = db.query("SELECT * FROM declinelens.scored")
    py = np.array([scoring.z_score(coef, r) for r in df.to_dict("records")])
    assert np.allclose(py, df["z"].to_numpy(), atol=1e-7)


def test_recourse_is_valid_and_cheapest(env):
    db, coef, z_cut = env
    plan_df = plans.build_plans()
    plan_rows = plan_df.to_dict("records")
    declined = db.query("SELECT * FROM declinelens.declined ORDER BY app_id LIMIT 60").to_dict("records")
    best = db.query("SELECT * FROM declinelens.recourse_best WHERE rn = 1").set_index("app_id")
    checked = 0
    for row in declined:
        feasible = [(p["effort"], p["n_moves"], p["plan_id"]) for p in plan_rows
                    if scoring.z_score(coef, row, p) >= z_cut]
        if not feasible:
            assert row["app_id"] not in best.index        # stranded in SQL <=> stranded in brute force
            continue
        want = min(feasible)
        got = best.loc[row["app_id"]]
        assert int(got["plan_id"]) == want[2]              # exact same cheapest plan
        chosen = next(p for p in plan_rows if p["plan_id"] == int(got["plan_id"]))
        assert scoring.z_score(coef, row, chosen) >= z_cut   # applying it really flips the decision
        checked += 1
    assert checked > 20


def test_top_reason_is_most_negative_contribution(env):
    db, _, _ = env
    r = db.query("SELECT app_id, contribution, rn FROM declinelens.decline_reasons")
    assert (r["contribution"] < 0).all()
    for _, g in r.groupby("app_id"):
        g = g.sort_values("rn")
        assert g["contribution"].is_monotonic_increasing


def test_protected_attributes_not_in_model(env):
    db, _, _ = env
    cols = set(db.query("SELECT * FROM declinelens.credit_model").columns)
    assert cols == set(model.COEF_COLS)
    assert not any(k in c for c in cols for k in ("gender", "age", "city"))


def test_audit_has_all_groups(env):
    db, _, _ = env
    a = db.query("SELECT * FROM declinelens.fairness_audit")
    assert set(a["dim_name"]) == {"gender", "city_tier", "age_band"}
    assert (a["impact_ratio"] <= 1.0 + 1e-9).all()

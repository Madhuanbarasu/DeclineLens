"""Synthetic loan-applicant generator. No real people, no employer data.

The generator deliberately bakes in a realistic *proxy effect*: career breaks make
employment history shorter for some applicants. Gender is never a model input, but the
audit can still surface unequal outcomes that arrive through proxy features.
"""
import numpy as np
import pandas as pd

APPLICANT_COLS = [
    "app_id", "gender", "city_tier", "age", "employment_years", "income_monthly",
    "credit_score", "utilization_pct", "enquiries_6m", "delinquencies_2y",
    "existing_emi", "loan_amount", "tenure_months", "repaid_ok",
]


def generate_applicants(n: int, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    gender = rng.choice(["F", "M"], n, p=[0.42, 0.58])
    city_tier = rng.choice([1, 2, 3], n, p=[0.35, 0.40, 0.25])
    age = np.clip(rng.normal(34, 8, n), 21, 62).round().astype(int)

    career_break = np.where(gender == "F", rng.exponential(1.6, n), rng.exponential(0.3, n))
    emp = np.clip((age - 21) * rng.uniform(0.35, 0.9, n) - career_break, 0, 40).round(1)

    income = np.exp(rng.normal(10.55 + 0.12 * (2 - city_tier) + 0.02 * emp, 0.45))
    income = np.round(np.clip(income, 12000, 400000) / 100) * 100

    cs = np.clip(rng.normal(610 + 28 * np.log(income / 20000) + 1.2 * emp, 55), 300, 900)
    cs = cs.round().astype(int)
    util = np.clip(rng.normal(45 - (cs - 650) * 0.12, 18), 0, 100).round()
    enq = rng.poisson(1.2 + (util > 60) * 1.0)
    dele = rng.poisson(np.where(cs < 600, 1.0, 0.12))

    emi = np.round(income * rng.uniform(0, 0.30, n) * (rng.random(n) < 0.65) / 100) * 100
    tenure = rng.choice([12, 24, 36, 48, 60, 72, 84], n, p=[.05, .15, .25, .20, .20, .10, .05])
    loan = np.round(income * 12 * rng.uniform(0.25, 2.5, n) / 1000) * 1000
    loan = np.clip(loan, 50000, 5000000)

    dti = (emi + loan / tenure) / income
    lti = loan / (income * 12)
    # Hidden "true" repayment process the model must learn from history.
    z = (1.6 + 0.012 * (cs - 650) - 0.018 * (util - 45) - 0.30 * (enq - 1.5)
         - 0.9 * dele + 0.06 * (emp - 6) - 3.0 * (dti - 0.3) - 0.35 * (lti - 1.2)
         + rng.logistic(0, 1, n))
    repaid = (z > 0).astype(int)

    return pd.DataFrame({
        "app_id": [f"A{i:08d}" for i in range(n)],
        "gender": gender, "city_tier": city_tier, "age": age,
        "employment_years": emp, "income_monthly": income,
        "credit_score": cs, "utilization_pct": util,
        "enquiries_6m": enq.astype(int), "delinquencies_2y": dele.astype(int),
        "existing_emi": emi, "loan_amount": loan, "tenure_months": tenure.astype(int),
        "repaid_ok": repaid,
    })[APPLICANT_COLS]

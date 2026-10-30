"""Tiny transparent credit model: logistic regression fitted with Newton's method (numpy only).

Protected attributes (gender, age, city tier) are NOT inputs. The model is linear on purpose:
every coefficient can be read, audited and shipped to the database as one row.
"""
import numpy as np
import pandas as pd

# (model column, feature name used in SQL / reason codes)
FEATURES = ["credit_score", "utilization", "enquiries", "delinquencies", "employment", "dti", "lti"]
COEF_COLS = ["b0"] + [f"b_{f}" for f in FEATURES]


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    dti = (df["existing_emi"] + df["loan_amount"] / df["tenure_months"]) / df["income_monthly"]
    lti = df["loan_amount"] / (df["income_monthly"] * 12)
    return np.column_stack([
        df["credit_score"], df["utilization_pct"], df["enquiries_6m"],
        df["delinquencies_2y"], df["employment_years"], dti, lti,
    ]).astype(float)


def train(df: pd.DataFrame, ridge: float = 1e-3, iters: int = 50) -> dict:
    X = feature_matrix(df)
    y = df["repaid_ok"].to_numpy(float)
    mu, sd = X.mean(0), X.std(0)
    Xs = np.column_stack([np.ones(len(X)), (X - mu) / sd])
    w = np.zeros(Xs.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-Xs @ w))
        grad = Xs.T @ (p - y) + ridge * w
        hess = (Xs * (p * (1 - p))[:, None]).T @ Xs + ridge * np.eye(len(w))
        step = np.linalg.solve(hess, grad)
        w -= step
        if np.abs(step).max() < 1e-9:
            break
    b = w[1:] / sd                      # back to raw feature scale
    b0 = w[0] - float(np.sum(w[1:] * mu / sd))
    return dict(zip(COEF_COLS, [b0, *b.tolist()]))


def coef_frame(coef: dict) -> pd.DataFrame:
    return pd.DataFrame([coef])[COEF_COLS]

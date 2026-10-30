"""Candidate 'what could the applicant change?' plans and plain-language reason texts.

Effort values are policy inputs (higher = harder or slower for the applicant). They are
heuristics a lender would tune; the database simply minimises them.
"""
import itertools

import pandas as pd

# feature -> list of (parameter, effort, text)
MOVES = {
    "loan": [(0.9, 1.0, "reduce the requested loan by 10%"), (0.8, 2.0, "reduce the requested loan by 20%"),
             (0.7, 3.0, "reduce the requested loan by 30%"), (0.6, 4.0, "reduce the requested loan by 40%"),
             (0.5, 5.0, "reduce the requested loan by 50%")],
    "tenure": [(12, 1.5, "extend the tenure by 12 months"), (24, 3.0, "extend the tenure by 24 months"),
               (36, 4.5, "extend the tenure by 36 months")],
    "emi": [(0.75, 3.0, "pay down 25% of your existing EMIs"), (0.50, 5.0, "pay down 50% of your existing EMIs"),
            (0.25, 7.0, "pay down 75% of your existing EMIs")],
    "util": [(10, 1.5, "lower credit-card utilisation by 10 points"), (20, 3.0, "lower credit-card utilisation by 20 points"),
             (30, 4.5, "lower credit-card utilisation by 30 points"), (40, 6.0, "lower credit-card utilisation by 40 points")],
    "score": [(20, 4.0, "raise your credit score by 20 points (a few months of on-time payments)"),
              (40, 6.0, "raise your credit score by 40 points (several months of on-time payments)"),
              (60, 8.0, "raise your credit score by 60 points (six months or more of on-time payments)")],
    "enq": [(1, 1.0, "wait for 1 recent credit enquiry to age out"), (2, 2.0, "wait for 2 recent credit enquiries to age out"),
            (3, 3.0, "wait for 3 recent credit enquiries to age out")],
}

PLAN_COLS = ["plan_id", "plan_desc", "n_moves", "effort", "loan_mult", "tenure_add",
             "emi_keep", "util_cut", "score_add", "enq_cut"]
_FIELD = {"loan": "loan_mult", "tenure": "tenure_add", "emi": "emi_keep",
          "util": "util_cut", "score": "score_add", "enq": "enq_cut"}
_DEFAULT = {"loan_mult": 1.0, "tenure_add": 0, "emi_keep": 1.0, "util_cut": 0.0, "score_add": 0, "enq_cut": 0}

REASON_TEXT = {
    "credit_score": "Your credit score is lower than that of typical approved applicants.",
    "utilization": "You are using a high share of your available credit-card limit.",
    "enquiries": "You have several recent credit enquiries, which can signal credit-seeking stress.",
    "delinquencies": "Your credit history shows recent missed or late payments.",
    "employment": "Your employment history is shorter than that of typical approved applicants.",
    "dti": "Your total monthly repayments would be high relative to your income.",
    "lti": "The loan you asked for is large relative to your annual income.",
}


def build_plans() -> pd.DataFrame:
    rows = []
    feats = list(MOVES)
    combos = [(f,) for f in feats] + list(itertools.combinations(feats, 2))
    pid = 1
    for combo in combos:
        for choice in itertools.product(*[MOVES[f] for f in combo]):
            row = dict(_DEFAULT)
            for f, (param, _eff, _txt) in zip(combo, choice):
                row[_FIELD[f]] = param
            rows.append({
                "plan_id": pid,
                "plan_desc": " and ".join(c[2] for c in choice),
                "n_moves": len(combo),
                "effort": float(sum(c[1] for c in choice)),
                **row,
            })
            pid += 1
    return pd.DataFrame(rows)[PLAN_COLS]


def reason_frame() -> pd.DataFrame:
    return pd.DataFrame({"feature": list(REASON_TEXT), "reason_text": list(REASON_TEXT.values())})

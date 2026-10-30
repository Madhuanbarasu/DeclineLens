"""Pure-Python reference implementation of the scoring + recourse maths.

The database does this at scale; this module exists so tests can prove the SQL is right.
"""


def z_score(c: dict, row, plan=None) -> float:
    loan_mult, tenure_add, emi_keep, util_cut, score_add, enq_cut = 1.0, 0, 1.0, 0.0, 0, 0
    if plan is not None:
        loan_mult, tenure_add, emi_keep = plan["loan_mult"], plan["tenure_add"], plan["emi_keep"]
        util_cut, score_add, enq_cut = plan["util_cut"], plan["score_add"], plan["enq_cut"]
    loan = row["loan_amount"] * loan_mult
    dti = (row["existing_emi"] * emi_keep + loan / (row["tenure_months"] + tenure_add)) / row["income_monthly"]
    lti = loan / (row["income_monthly"] * 12)
    return (c["b0"]
            + c["b_credit_score"] * min(row["credit_score"] + score_add, 900)
            + c["b_utilization"] * max(row["utilization_pct"] - util_cut, 0)
            + c["b_enquiries"] * max(row["enquiries_6m"] - enq_cut, 0)
            + c["b_delinquencies"] * row["delinquencies_2y"]
            + c["b_employment"] * row["employment_years"]
            + c["b_dti"] * dti
            + c["b_lti"] * lti)

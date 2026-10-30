"""Look up one applicant's decision, reasons and recourse, and write the customer letter."""
import re


def _safe_id(app_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,20}", app_id):
        raise ValueError("invalid applicant id")
    return app_id


def get_case(db, app_id: str) -> dict:
    app_id = _safe_id(app_id)
    s = db.query(f"SELECT * FROM declinelens.scored WHERE app_id = '{app_id}'")
    if s.empty:
        raise KeyError(app_id)
    applicant = s.iloc[0].to_dict()
    reasons = db.query(
        "SELECT r.rn, r.feature, r.contribution, t.reason_text "
        "FROM declinelens.decline_reasons r JOIN declinelens.reason_text t ON r.feature = t.feature "
        f"WHERE r.app_id = '{app_id}' ORDER BY r.rn")
    plans = db.query(
        "SELECT b.rn, b.effort, b.z_new, p.plan_desc "
        "FROM declinelens.recourse_best b JOIN declinelens.recourse_plans p ON b.plan_id = p.plan_id "
        f"WHERE b.app_id = '{app_id}' ORDER BY b.rn")
    cut = db.scalar("SELECT cutoff FROM declinelens.run_config")
    return {"applicant": applicant, "reasons": reasons, "plans": plans, "cutoff": float(cut)}


def build_letter(case: dict) -> str:
    a = case["applicant"]
    loan = f"Rs {a['loan_amount']:,.0f}"
    if a["decision"] == "APPROVED":
        return (f"Application {a['app_id']}: your request for {loan} over {int(a['tenure_months'])} months "
                f"is approved.")
    lines = [f"Application {a['app_id']}: your request for {loan} over {int(a['tenure_months'])} months "
             "could not be approved at this time.", "",
             "The main reasons, in order of impact:"]
    for _, r in case["reasons"].iterrows():
        lines.append(f"  {int(r['rn'])}. {r['reason_text']}")
    lines.append("")
    if case["plans"].empty:
        lines.append("None of the changes we can model would lead to approval. Please speak to a branch "
                     "officer, who can review your application manually.")
    else:
        lines.append("What could change this decision (easiest first):")
        for _, p in case["plans"].iterrows():
            lines.append(f"  Option {int(p['rn'])}: {p['plan_desc']}.")
        lines.append("")
        lines.append("These are estimates from our scoring model, not a guarantee of approval.")
    return "\n".join(lines)

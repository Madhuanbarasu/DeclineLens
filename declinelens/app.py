"""DeclineLens dashboard.  Run from the project root:  streamlit run declinelens/app.py
Backend comes from the BACKEND env var (exasol | duckdb)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from declinelens import explain
from declinelens.db import DB

st.set_page_config(page_title="DeclineLens", layout="wide")
BACKEND = os.environ.get("BACKEND", "exasol")


@st.cache_resource
def get_db():
    return DB(BACKEND, read_only=(BACKEND == "duckdb"))


db = get_db()
st.title("DeclineLens")
st.caption("Every declined applicant gets the reasons and the cheapest path to yes, computed inside "
           f"the database ({BACKEND}). All data is synthetic.")

tab1, tab2, tab3 = st.tabs(["Explain a decision", "Fairness audit", "Under the hood"])

with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("Pick a random declined applicant") or "app_id" not in st.session_state:
            st.session_state["app_id"] = db.scalar(
                "SELECT app_id FROM declinelens.recourse_best WHERE rn = 1 ORDER BY app_id "
                f"LIMIT 1 OFFSET {int(pd.Timestamp.now().microsecond) % 500}")
        app_id = st.text_input("Applicant ID", st.session_state["app_id"])
    try:
        case = explain.get_case(db, app_id)
    except (KeyError, ValueError):
        st.warning("Applicant not found.")
        st.stop()
    a = case["applicant"]
    with c1:
        st.metric("Decision", a["decision"])
        st.metric("Repayment probability", f"{a['p_repay']:.1%}")
        st.caption(f"Approval cutoff: {case['cutoff']:.0%}")
        st.write(f"Loan Rs {a['loan_amount']:,.0f} over {int(a['tenure_months'])} months  \n"
                 f"Income Rs {a['income_monthly']:,.0f}/month, credit score {int(a['credit_score'])}")
    with c2:
        st.subheader("Why")
        st.dataframe(case["reasons"][["rn", "reason_text"]].rename(columns={"rn": "#", "reason_text": "Reason"}),
                     hide_index=True, width="stretch")
        st.subheader("What could change the decision")
        if case["plans"].empty:
            st.info("No modelled path to approval. Route to manual review.")
        else:
            st.dataframe(case["plans"][["rn", "plan_desc", "effort"]].rename(
                columns={"rn": "Option", "plan_desc": "Change", "effort": "Effort score"}),
                hide_index=True, width="stretch")
    st.subheader("Letter to the customer")
    letter = explain.build_letter(case)
    st.code(letter, language=None)
    st.download_button("Download letter", letter, f"{a['app_id']}_letter.txt")

with tab2:
    st.write("The model never sees gender, age or city. This audit checks whether outcomes and "
             "*recourse* still differ by group through proxy features.")
    audit = db.query("SELECT * FROM declinelens.fairness_audit ORDER BY dim_name, grp")
    for col in ["n", "declined_n", "approval_rate", "impact_ratio", "stranded_pct", "avg_best_effort"]:
        audit[col] = pd.to_numeric(audit[col])
    audit["approval_rate"] = (audit["approval_rate"] * 100).round(1)
    audit["stranded_pct"] = (audit["stranded_pct"] * 100).round(1)
    audit["impact_ratio"] = audit["impact_ratio"].round(2)
    audit["avg_best_effort"] = audit["avg_best_effort"].round(2)
    st.dataframe(audit.rename(columns={
        "dim_name": "Dimension", "grp": "Group", "n": "Applicants", "approval_rate": "Approval rate (%)",
        "impact_ratio": "Impact ratio vs best group", "declined_n": "Declined",
        "stranded_pct": "Declined with no path (%)", "avg_best_effort": "Avg effort of easiest path"}),
        hide_index=True, width="stretch")
    flagged = audit[audit["impact_ratio"] < 0.8]
    if len(flagged):
        st.error("Impact ratio below 0.8 (four-fifths screen): "
                 + ", ".join(f"{r.dim_name} = {r.grp}" for r in flagged.itertuples()))
    st.bar_chart(audit.assign(label=audit["dim_name"] + ": " + audit["grp"]).set_index("label")["approval_rate"])
    st.bar_chart(audit.assign(label=audit["dim_name"] + ": " + audit["grp"]).set_index("label")["avg_best_effort"])

with tab3:
    st.write("Pipeline stages, timed in the database:")
    stats = db.query("SELECT stage_name, row_count, elapsed_s FROM declinelens.run_stats")
    stats["row_count"] = pd.to_numeric(stats["row_count"])
    st.dataframe(stats, hide_index=True, width="stretch")
    st.code(open(Path(__file__).resolve().parent.parent / "sql" / "04_recourse.sql").read(), language="sql")
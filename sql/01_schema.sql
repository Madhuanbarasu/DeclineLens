-- DeclineLens schema. Plain ANSI-style SQL: runs on Exasol Personal and (for tests) DuckDB.
CREATE SCHEMA IF NOT EXISTS declinelens;

CREATE OR REPLACE TABLE declinelens.applicants (
    app_id           VARCHAR(12),
    gender           VARCHAR(1),
    city_tier        INTEGER,
    age              INTEGER,
    employment_years DOUBLE,
    income_monthly   DOUBLE,
    credit_score     INTEGER,
    utilization_pct  DOUBLE,
    enquiries_6m     INTEGER,
    delinquencies_2y INTEGER,
    existing_emi     DOUBLE,
    loan_amount      DOUBLE,
    tenure_months    INTEGER,
    repaid_ok        INTEGER
);

CREATE OR REPLACE TABLE declinelens.credit_model (
    b0 DOUBLE, b_credit_score DOUBLE, b_utilization DOUBLE, b_enquiries DOUBLE,
    b_delinquencies DOUBLE, b_employment DOUBLE, b_dti DOUBLE, b_lti DOUBLE
);

CREATE OR REPLACE TABLE declinelens.run_config (cutoff DOUBLE, z_cut DOUBLE);

CREATE OR REPLACE TABLE declinelens.recourse_plans (
    plan_id    INTEGER,
    plan_desc  VARCHAR(400),
    n_moves    INTEGER,
    effort     DOUBLE,
    loan_mult  DOUBLE,
    tenure_add INTEGER,
    emi_keep   DOUBLE,
    util_cut   DOUBLE,
    score_add  INTEGER,
    enq_cut    INTEGER
);

CREATE OR REPLACE TABLE declinelens.reason_text (
    feature     VARCHAR(30),
    reason_text VARCHAR(300)
);

CREATE OR REPLACE TABLE declinelens.run_stats (
    stage_name VARCHAR(60),
    row_count  DECIMAL(18,0),
    elapsed_s  DOUBLE
);

-- Step 3: counterfactual recourse, as one relational problem.
-- Every declined applicant is crossed with every candidate plan, each pair is re-scored, and
-- we keep the three lowest-effort plans that flip the decision. With ~200 plans, 100k declined
-- applicants means ~20 million what-if evaluations in a single set-based statement.
CREATE OR REPLACE TABLE declinelens.recourse_best AS
SELECT app_id, plan_id, effort, z_new, rn
FROM (
    SELECT e.app_id, e.plan_id, e.effort, e.z_new,
           ROW_NUMBER() OVER (PARTITION BY e.app_id ORDER BY e.effort, e.n_moves, e.plan_id) AS rn
    FROM (
        SELECT d.app_id, p.plan_id, p.effort, p.n_moves,
               m.b0
               + m.b_credit_score * LEAST(d.credit_score + p.score_add, 900)
               + m.b_utilization * GREATEST(d.utilization_pct - p.util_cut, 0)
               + m.b_enquiries * GREATEST(d.enquiries_6m - p.enq_cut, 0)
               + m.b_delinquencies * d.delinquencies_2y
               + m.b_employment * d.employment_years
               + m.b_dti * ((d.existing_emi * p.emi_keep
                             + d.loan_amount * p.loan_mult / (d.tenure_months + p.tenure_add)) / d.income_monthly)
               + m.b_lti * (d.loan_amount * p.loan_mult / (d.income_monthly * 12)) AS z_new
        FROM declinelens.declined d
        CROSS JOIN declinelens.recourse_plans p
        CROSS JOIN declinelens.credit_model m
    ) e
    WHERE e.z_new >= (SELECT z_cut FROM declinelens.run_config)
) f
WHERE rn <= 3;

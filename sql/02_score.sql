-- Step 1: score every applicant inside the database and apply the decision cutoff.
CREATE OR REPLACE TABLE declinelens.scored AS
SELECT t.*,
       1.0 / (1.0 + EXP(-t.z)) AS p_repay,
       CASE WHEN t.z >= c.z_cut THEN 'APPROVED' ELSE 'DECLINED' END AS decision
FROM (
    SELECT a.app_id, a.gender, a.city_tier, a.age, a.employment_years, a.income_monthly,
           a.credit_score, a.utilization_pct, a.enquiries_6m, a.delinquencies_2y,
           a.existing_emi, a.loan_amount, a.tenure_months, a.dti, a.lti,
           m.b0
           + m.b_credit_score * a.credit_score
           + m.b_utilization * a.utilization_pct
           + m.b_enquiries * a.enquiries_6m
           + m.b_delinquencies * a.delinquencies_2y
           + m.b_employment * a.employment_years
           + m.b_dti * a.dti
           + m.b_lti * a.lti AS z
    FROM (
        SELECT b.*,
               (b.existing_emi + b.loan_amount / b.tenure_months) / b.income_monthly AS dti,
               b.loan_amount / (b.income_monthly * 12) AS lti
        FROM declinelens.applicants b
    ) a
    CROSS JOIN declinelens.credit_model m
) t
CROSS JOIN declinelens.run_config c;

CREATE OR REPLACE VIEW declinelens.declined AS
SELECT * FROM declinelens.scored WHERE decision = 'DECLINED';

-- Reference point for reason codes: the average approved applicant.
CREATE OR REPLACE TABLE declinelens.ref_means AS
SELECT AVG(credit_score)     AS credit_score,
       AVG(utilization_pct)  AS utilization,
       AVG(enquiries_6m)     AS enquiries,
       AVG(delinquencies_2y) AS delinquencies,
       AVG(employment_years) AS employment,
       AVG(dti)              AS dti,
       AVG(lti)              AS lti
FROM declinelens.scored
WHERE decision = 'APPROVED';

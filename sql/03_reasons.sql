-- Step 2: reason codes. For a linear model, coefficient x (value - approved average)
-- is each feature's exact contribution to the gap. The three most negative are the reasons.
CREATE OR REPLACE TABLE declinelens.decline_reasons AS
SELECT app_id, feature, contribution, rn
FROM (
    SELECT c.app_id, c.feature, c.contribution,
           ROW_NUMBER() OVER (PARTITION BY c.app_id ORDER BY c.contribution, c.feature) AS rn
    FROM (
        SELECT d.app_id, 'credit_score' AS feature, m.b_credit_score * (d.credit_score - r.credit_score) AS contribution
        FROM declinelens.declined d CROSS JOIN declinelens.credit_model m CROSS JOIN declinelens.ref_means r
        UNION ALL
        SELECT d.app_id, 'utilization', m.b_utilization * (d.utilization_pct - r.utilization)
        FROM declinelens.declined d CROSS JOIN declinelens.credit_model m CROSS JOIN declinelens.ref_means r
        UNION ALL
        SELECT d.app_id, 'enquiries', m.b_enquiries * (d.enquiries_6m - r.enquiries)
        FROM declinelens.declined d CROSS JOIN declinelens.credit_model m CROSS JOIN declinelens.ref_means r
        UNION ALL
        SELECT d.app_id, 'delinquencies', m.b_delinquencies * (d.delinquencies_2y - r.delinquencies)
        FROM declinelens.declined d CROSS JOIN declinelens.credit_model m CROSS JOIN declinelens.ref_means r
        UNION ALL
        SELECT d.app_id, 'employment', m.b_employment * (d.employment_years - r.employment)
        FROM declinelens.declined d CROSS JOIN declinelens.credit_model m CROSS JOIN declinelens.ref_means r
        UNION ALL
        SELECT d.app_id, 'dti', m.b_dti * (d.dti - r.dti)
        FROM declinelens.declined d CROSS JOIN declinelens.credit_model m CROSS JOIN declinelens.ref_means r
        UNION ALL
        SELECT d.app_id, 'lti', m.b_lti * (d.lti - r.lti)
        FROM declinelens.declined d CROSS JOIN declinelens.credit_model m CROSS JOIN declinelens.ref_means r
    ) c
    WHERE c.contribution < 0
) x
WHERE rn <= 3;

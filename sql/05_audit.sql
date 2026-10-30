-- Step 4: fairness audit. Protected attributes are not model inputs, but outcomes and
-- *recourse* can still differ by group through proxies. We measure both:
--   approval_rate / impact_ratio : who gets approved (4/5ths-style screen)
--   stranded_pct                 : declined applicants with NO modelled path to approval
--   avg_best_effort              : how hard the easiest path is, on average
CREATE OR REPLACE VIEW declinelens.grp_base AS
SELECT app_id, decision, 'gender' AS dim_name, gender AS grp FROM declinelens.scored
UNION ALL
SELECT app_id, decision, 'city_tier', 'Tier ' || CAST(city_tier AS VARCHAR(2)) FROM declinelens.scored
UNION ALL
SELECT app_id, decision, 'age_band',
       CASE WHEN age < 30 THEN 'under 30' WHEN age < 45 THEN '30-44' ELSE '45+' END
FROM declinelens.scored;

CREATE OR REPLACE TABLE declinelens.fairness_audit AS
SELECT t.dim_name, t.grp, t.n, t.approval_rate,
       t.approval_rate / MAX(t.approval_rate) OVER (PARTITION BY t.dim_name) AS impact_ratio,
       t.declined_n, t.stranded_pct, t.avg_best_effort
FROM (
    SELECT g.dim_name, g.grp, COUNT(*) AS n,
           AVG(CASE WHEN g.decision = 'APPROVED' THEN 1.0 ELSE 0.0 END) AS approval_rate,
           SUM(CASE WHEN g.decision = 'DECLINED' THEN 1 ELSE 0 END) AS declined_n,
           AVG(CASE WHEN g.decision = 'DECLINED' AND r.app_id IS NULL THEN 1.0
                    WHEN g.decision = 'DECLINED' THEN 0.0 END) AS stranded_pct,
           AVG(r.effort) AS avg_best_effort
    FROM declinelens.grp_base g
    LEFT JOIN (SELECT app_id, effort FROM declinelens.recourse_best WHERE rn = 1) r
           ON g.app_id = r.app_id
    GROUP BY g.dim_name, g.grp
) t;

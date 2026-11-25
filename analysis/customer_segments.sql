-- Import the IBM Telco Customer Churn CSV into a table named customers.
SELECT Contract, COUNT(*) AS customers,
       SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned,
       100.0 * AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0.0 END) AS churn_pct,
       AVG(CAST(MonthlyCharges AS REAL)) AS avg_monthly_charge
FROM customers GROUP BY Contract ORDER BY churn_pct DESC;

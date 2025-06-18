-- 用户的复杂逾期率分析查询
with dates as(
select date_format(id,'%Y-%m') as month_yyyy_mm, last_date_of_month as month_last_day from calendar
where id>='2024-01-01' and id<'2024-10-01' and id = last_date_of_month
)

SELECT
  substr(loan_active_date, 1, 7) AS loan_month,
  b.product_id,
  loan_init_term,
  strategy,
  output_level,
  (YEAR(month_last_day) - YEAR(loan_active_date)) * 12 + MONTH(month_last_day) - MONTH(loan_active_date) AS mob,
  month_yyyy_mm AS stat_month,
  count(1) AS nbr_bills
FROM
  orange.lending_details b
  JOIN dates ON 1 = 1
  JOIN (
    SELECT
      due_bill_no,
      product_id,
      remain_principal,
      paid_principal,
      paid_interest,
      remain_interest,
      dpd_days,
      loan_term_remain,
      s_d_date,
      e_d_date,
      project_id
    FROM
      orange.loan_info
  ) c ON b.due_bill_no = c.due_bill_no
  AND b.project_id  = c.project_id 
  LEFT JOIN (
    SELECT
      t.swift_no,
      t.pro_code,
      t.applyno,
      t.createtime,
      t.fitscore,
      t.retcode,
      t.scorerange,
      t.strategy,
      w.output_level
    FROM
      (SELECT applyno, max(id) AS id_a FROM orange.t_ws_entrance_credit  GROUP BY applyno) m
      LEFT JOIN (
        SELECT
          swift_no,
          applyno,
          id,
          pro_code,
          fitscore,
          scorerange,
          retcode,
          strategy,
          createTime
        FROM
          orange.t_ws_entrance_credit
      ) t ON m.applyno = t.applyno
      AND m.id_a = t.id
      LEFT JOIN (SELECT swift_no, output_level FROM orange.t_model_inputparams_extend2) w ON t.swift_no = w.swift_no
  ) t1 ON b.due_bill_no = t1.applyno
WHERE
  is_lend=1
  AND (month_last_day BETWEEN c.s_d_date AND date_sub(c.e_d_date, INTERVAL 1 DAY))
GROUP BY
  substr(loan_active_date, 1, 7),
  (YEAR(month_last_day) - YEAR(loan_active_date)) * 12 + MONTH(month_last_day) - MONTH(loan_active_date),
  month_yyyy_mm,
  b.product_id,
  loan_init_term,
  strategy,
  output_level
LIMIT 50; 
#!/bin/bash

echo "🔍 DB-GPT 自动化分析报告生成器"
echo "================================"

# 配置
DBGPT_URL="http://localhost:5670"
MODEL="deepseek"
CHAT_PARAM="orange"

# 函数：执行SQL查询
execute_sql() {
    local sql_query="$1"
    echo "📊 执行SQL查询..."
    
    curl -s -X POST "${DBGPT_URL}/api/v2/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer EMPTY" \
        -d "{
            \"model\": \"${MODEL}\",
            \"messages\": [{\"role\": \"user\", \"content\": \"${sql_query}\"}],
            \"chat_mode\": \"chat_with_db_execute\",
            \"chat_param\": \"${CHAT_PARAM}\",
            \"stream\": false,
            \"max_tokens\": 2000
        }" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    content = data['choices'][0]['message']['content']
    print(content)
except:
    print('SQL执行失败')
"
}

# 函数：生成分析报告
generate_report() {
    local data_summary="$1"
    echo "📝 生成分析报告..."
    
    curl -s -X POST "${DBGPT_URL}/api/v2/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer EMPTY" \
        -d "{
            \"model\": \"${MODEL}\",
            \"messages\": [{\"role\": \"user\", \"content\": \"请对以下贷款数据进行详细分析并生成专业的业务分析报告，包括产品表现、策略效果、趋势分析和业务建议：${data_summary}\"}],
            \"chat_mode\": \"chat_normal\",
            \"stream\": false,
            \"max_tokens\": 3000
        }" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    content = data['choices'][0]['message']['content']
    print(content)
except Exception as e:
    print(f'报告生成失败: {e}')
"
}

# 主程序
main() {
    echo "请选择操作："
    echo "1. 执行预设的逾期率分析SQL"
    echo "2. 自定义SQL查询"
    echo "3. 直接输入数据生成报告"
    
    read -p "请输入选择 (1-3): " choice
    
    case $choice in
        1)
            echo "🎯 执行预设的逾期率分析查询..."
            sql="WITH dates AS (
                SELECT DATE_FORMAT(id, '%Y-%m') AS month_yyyy_mm, 
                       last_date_of_month AS month_last_day 
                FROM calendar
                WHERE id >= '2024-01-01' AND id < '2024-10-01' 
                  AND id = last_date_of_month
            )
            SELECT
                SUBSTR(loan_active_date, 1, 7) AS loan_month,
                b.product_id,
                loan_init_term,
                strategy,
                output_level,
                (YEAR(month_last_day) - YEAR(loan_active_date)) * 12 + 
                 MONTH(month_last_day) - MONTH(loan_active_date) AS mob,
                month_yyyy_mm AS stat_month,
                COUNT(1) AS nbr_bills
            FROM orange.lending_details b
            JOIN dates ON 1 = 1
            JOIN (
                SELECT due_bill_no, product_id, remain_principal, paid_principal,
                       paid_interest, remain_interest, dpd_days, loan_term_remain,
                       s_d_date, e_d_date, project_id
                FROM orange.loan_info
            ) c ON b.due_bill_no = c.due_bill_no AND b.project_id = c.project_id
            LEFT JOIN (
                SELECT t.swift_no, t.pro_code, t.applyno, t.createtime,
                       t.fitscore, t.retcode, t.scorerange, t.strategy, w.output_level
                FROM (
                    SELECT applyno, MAX(id) AS id_a 
                    FROM orange.t_ws_entrance_credit 
                    GROUP BY applyno
                ) m
                LEFT JOIN (
                    SELECT swift_no, applyno, id, pro_code, fitscore,
                           scorerange, retcode, strategy, createTime
                    FROM orange.t_ws_entrance_credit
                ) t ON m.applyno = t.applyno AND m.id_a = t.id
                LEFT JOIN (
                    SELECT swift_no, output_level 
                    FROM orange.t_model_inputparams_extend2
                ) w ON t.swift_no = w.swift_no
            ) t1 ON b.due_bill_no = t1.applyno
            WHERE is_lend = 1 
              AND (month_last_day BETWEEN c.s_d_date AND DATE_SUB(c.e_d_date, INTERVAL 1 DAY))
            GROUP BY SUBSTR(loan_active_date, 1, 7), 
                     (YEAR(month_last_day) - YEAR(loan_active_date)) * 12 + 
                      MONTH(month_last_day) - MONTH(loan_active_date),
                     month_yyyy_mm, b.product_id, loan_init_term, strategy, output_level
            LIMIT 10;"
            
            result=$(execute_sql "$sql")
            echo "✅ SQL执行结果："
            echo "$result"
            echo ""
            
            # 提取关键数据用于报告生成
            data_summary="基于SQL查询结果的贷款数据：包含放款月份、产品ID、贷款期限、策略、输出等级、MOB、统计月份和账单数量等维度的分析数据。"
            
            echo "🎯 生成分析报告..."
            report=$(generate_report "$data_summary")
            echo "✅ 分析报告："
            echo "$report"
            ;;
            
        2)
            echo "请输入您的SQL查询："
            read -r sql_input
            result=$(execute_sql "$sql_input")
            echo "✅ SQL执行结果："
            echo "$result"
            
            echo ""
            echo "🎯 生成基于查询结果的分析报告..."
            report=$(generate_report "SQL查询结果：$result")
            echo "✅ 分析报告："
            echo "$report"
            ;;
            
        3)
            echo "请输入要分析的数据："
            read -r data_input
            report=$(generate_report "$data_input")
            echo "✅ 分析报告："
            echo "$report"
            ;;
            
        *)
            echo "❌ 无效选择"
            exit 1
            ;;
    esac
}

# 运行主程序
main 
"""
增强的输出解析器修复 - 解决AI模型响应格式问题
"""

import re
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SQLResponseFixer:
    """SQL响应修复器"""
    
    def __init__(self):
        self.sql_keywords = ['WITH', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'SHOW', 'DESCRIBE', 'EXPLAIN']
    
    def extract_sql_from_user_input(self, user_input: str) -> str:
        """从用户输入中提取SQL语句"""
        if not user_input:
            return ""
        
        # 查找SQL关键词开始的位置
        for keyword in self.sql_keywords:
            pattern = rf'\b{keyword}\b'
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                # 找到SQL开始位置
                start_pos = match.start()
                # 提取SQL部分
                sql_part = user_input[start_pos:]
                
                # 移除末尾的非SQL文字
                stop_phrases = ['执行代码', '并分析', '生成报告', '请执行', '运行这个']
                for phrase in stop_phrases:
                    if phrase in sql_part:
                        sql_part = sql_part.split(phrase)[0]
                
                # 清理SQL
                sql_part = sql_part.strip()
                if not sql_part.endswith(';'):
                    sql_part += ';'
                
                logger.info(f"从用户输入中提取到SQL: {sql_part[:100]}...")
                return sql_part
        
        return user_input
    
    def is_descriptive_text(self, sql: str) -> bool:
        """检查是否为描述性文字而非SQL"""
        if not sql:
            return True
        
        # 描述性文字的特征
        descriptive_patterns = [
            r'您提供的.*查询',
            r'已经正确编写',
            r'可以直接执行',
            r'生成.*报告',
            r'The.*query.*is',
            r'SQL.*statement.*is'
        ]
        
        for pattern in descriptive_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                logger.warning(f"检测到描述性文字: {sql[:50]}...")
                return True
        
        # 检查是否包含SQL关键词
        has_sql_keywords = any(keyword.upper() in sql.upper() for keyword in self.sql_keywords)
        if not has_sql_keywords:
            logger.warning(f"未检测到SQL关键词: {sql[:50]}...")
            return True
        
        return False
    
    def fix_response(self, response_dict: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """修复AI模型响应"""
        if not isinstance(response_dict, dict):
            return response_dict
        
        sql = response_dict.get('sql', '')
        
        # 如果sql字段包含描述性文字，尝试从用户输入中提取实际SQL
        if self.is_descriptive_text(sql):
            logger.info("检测到描述性文字，尝试从用户输入中提取SQL...")
            extracted_sql = self.extract_sql_from_user_input(user_input)
            
            if extracted_sql and not self.is_descriptive_text(extracted_sql):
                response_dict['sql'] = extracted_sql
                logger.info(f"成功修复SQL: {extracted_sql[:100]}...")
                
                # 更新thoughts和direct_response
                if 'thoughts' in response_dict:
                    response_dict['thoughts'] = f"已从用户输入中提取并修复SQL查询: {extracted_sql[:50]}..."
                
                if 'direct_response' in response_dict:
                    response_dict['direct_response'] = "SQL查询已修复并准备执行。"
            else:
                logger.error("无法从用户输入中提取有效的SQL")
                response_dict['sql'] = ""
                response_dict['direct_response'] = "抱歉，无法识别有效的SQL查询，请检查您的输入。"
        
        return response_dict

def patch_out_parser():
    """为out_parser.py添加修复功能"""
    
    patch_code = '''
# === SQL响应修复器补丁 ===
from enhanced_out_parser_fix import SQLResponseFixer

# 在DbChatOutputParser类中添加修复器
if not hasattr(DbChatOutputParser, '_sql_fixer'):
    DbChatOutputParser._sql_fixer = SQLResponseFixer()

# 修补parse_prompt_response方法
original_parse_prompt_response = DbChatOutputParser.parse_prompt_response

def patched_parse_prompt_response(self, model_out_text, user_input: str = ""):
    """修补的响应解析方法"""
    try:
        # 调用原始方法
        result = original_parse_prompt_response(self, model_out_text, user_input)
        
        # 如果结果是字典，尝试修复
        if isinstance(result, dict):
            result = self._sql_fixer.fix_response(result, user_input)
        
        return result
    except Exception as e:
        logger.error(f"响应解析修复失败: {e}")
        return original_parse_prompt_response(self, model_out_text, user_input)

# 应用补丁
DbChatOutputParser.parse_prompt_response = patched_parse_prompt_response
logger.info("SQL响应修复器补丁已应用")
'''
    
    return patch_code

if __name__ == "__main__":
    # 测试修复器
    fixer = SQLResponseFixer()
    
    # 测试用例1: 描述性文字
    test_response = {
        "sql": "您提供的SQL查询已经正确编写，可以直接执行以获取数据并生成逾期率报告。",
        "thoughts": "用户提供了复杂的SQL查询",
        "display_type": "Table"
    }
    
    test_user_input = """with dates as(
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
  ;
执行代码,并分析逾期率,生成报告"""
    
    fixed_response = fixer.fix_response(test_response, test_user_input)
    print("修复结果:")
    print(f"SQL: {fixed_response['sql'][:200]}...")
    print(f"是否包含实际SQL: {not fixer.is_descriptive_text(fixed_response['sql'])}")

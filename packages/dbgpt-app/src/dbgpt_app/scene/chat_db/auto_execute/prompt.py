import json

from dbgpt._private.config import Config
from dbgpt.core import (
    ChatPromptTemplate,
    HumanPromptTemplate,
    MessagesPlaceholder,
    SystemPromptTemplate,
)
from dbgpt_app.scene import AppScenePromptTemplateAdapter, ChatScene
from dbgpt_app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser

CFG = Config()


_PROMPT_SCENE_DEFINE_EN = "You are a database expert. "
_PROMPT_SCENE_DEFINE_ZH = "你是一个数据库专家. "

_DEFAULT_TEMPLATE_EN = """
Please answer the user's question based on the database selected by the user and some \
of the available table structure definitions of the database.
Database name:
     {db_name}
Table structure definition:
     {table_info}

CRITICAL CONSTRAINTS:
    1. ONLY use columns that are explicitly listed in the table structure definition above. \
    DO NOT assume or invent column names that are not shown.
    2. Please understand the user's intention based on the user's question, and use the \
    given table structure definition to create a grammatically correct {dialect} sql. \
    If sql is not required, answer the user's question directly.
    3. Always limit the query to a maximum of {top_k} results unless the user specifies \
    in the question the specific number of rows of data he wishes to obtain.
    4. You can only use the tables provided in the table structure information to \
    generate sql. If you cannot generate sql based on the provided table structure, \
    please analyze user requirements and proactively suggest missing information:\
    - Analyze the specific business goal the user wants to achieve\
    - Identify which key fields or tables are missing from the current table structure\
    - Clearly inform the user what additional information is needed\
    - Suggest possible solutions or alternative query approaches\
    - Provide detailed guidance in the direct_response field\
    It is prohibited to fabricate information at will.
    5. Please be careful not to mistake the relationship between tables and columns when\
     generating SQL. Double-check that every column referenced in your SQL exists in the \
     table structure definition.
    6. Please check the correctness of the SQL and ensure that the query performance is\
     optimized under correct conditions.
    7. If the user asks for date-related queries but no date columns are available, \
    explain that the current table structure doesn't contain date information.
    8. Please choose the best one from the display methods given below for data \
    rendering, and put the type name into the name parameter value that returns \
    the required format. If you cannot find the most suitable one, use 'Table' as \
    the display method. , the available data display methods are as follows: \
    {display_type}
    9. If the user explicitly requests "analysis", "report", "summary" or similar \
    in-depth analysis needs, please provide a detailed analysis report in the \
    analysis_report field, including:\
    - summary: Brief summary of analysis results\
    - key_findings: Key facts and trends discovered from the data\
    - insights: Business insights and explanations based on the data\
    - recommendations: Specific recommendations based on analysis results\
    - methodology: Explanation of analysis methods and logic\
    If the user is just making a simple data query, analysis_report can be empty or omitted.
    
User Question:
    {user_input}
Please think step by step and respond according to the following JSON format:
    {response_format}
Ensure the response is correct json and can be parsed by Python json.loads.

"""

_DEFAULT_TEMPLATE_ZH = """
请根据用户选择的数据库和该库的部分可用表结构定义来回答用户问题.
数据库名:
    {db_name}
表结构定义:
    {table_info}

关键约束:
    1. 只能使用上述表结构定义中明确列出的列名。不要假设或创造未显示的列名。
    2. 请根据用户问题理解用户意图，使用给出表结构定义    创建一个语法正确的mysql sql，如果不需要sql，则直接回答用户问题。
    3. 除非用户在问题中指定了他希望获得的具体数据行数，否则始终将查询限制为最多     50 个结果。
    4. 只能使用表结构信息中提供的表来生成 sql。如果无法根据提供的表结构生成 sql，    请分析用户需求并主动提示缺少的信息：    - 分析用户想要实现的具体业务目标    - 识别当前表结构中缺少哪些关键字段或表    - 明确告知用户需要提供什么额外信息    - 建议可能的解决方案或替代查询方式    - 在direct_response中提供详细的指导信息    禁止随意捏造信息。
    5. 请注意生成SQL时不要弄错表和列的关系，仔细检查SQL中引用的每个列都存在于表结构定义中。
    6. 请检查SQL的正确性，并保证正确的情况下优化查询性能
    7. 如果用户询问日期相关查询但没有可用的日期列，请解释当前表结构不包含日期信息。
    8. 请从如下给出的展示方式种选择最优的一种用以进行数据渲染，    将类型名称放入返回要求格式的name参数值中，如果找不到最合适的    则使用'Table'作为展示方式，可用数据展示方式如下: {display_type}
    9. 如果用户明确要求"分析"、"报告"、"总结"或类似的深度分析需求，    请在analysis_report字段中提供详细的分析报告，包括：    - summary: 分析结果的简要总结    - key_findings: 从数据中发现的关键事实和趋势    - insights: 基于数据的业务洞察和解释    - recommendations: 基于分析结果的具体建议    - methodology: 分析方法和逻辑的说明    如果用户只是简单查询数据，analysis_report可以为空或省略。
    10. **重要：为了提高查询结果的可读性，请遵循以下SQL格式化规则：**
        - 使用中文别名：为所有字段添加有意义的中文别名，如 `field_name AS '中文名称'`
        - 格式化数值：
          * 百分比字段使用 `CONCAT(ROUND(field * 100, 2), '%') AS '百分比'`
          * 金额字段使用 `CONCAT('¥', FORMAT(amount_field, 2)) AS '金额'`
          * 日期字段使用 `DATE_FORMAT(date_field, '%Y-%m-%d') AS '日期'`
        - 避免复杂的JOIN：如果JOIN条件可能导致大量NULL值，优先使用单表查询
        - 确保字段类型匹配：VARCHAR日期字段与DATE字段比较时要注意格式转换
        - 按重要性排序：使用 ORDER BY 将最重要的结果排在前面
用户问题:
    {user_input}


请一步步思考并按照以下JSON格式回复：
    {response_format}
确保返回正确的json并且可以被Python json.loads方法解析.

"""

_DEFAULT_TEMPLATE = (
    _DEFAULT_TEMPLATE_EN if CFG.LANGUAGE == "en" else _DEFAULT_TEMPLATE_ZH
)

PROMPT_SCENE_DEFINE = (
    _PROMPT_SCENE_DEFINE_EN if CFG.LANGUAGE == "en" else _PROMPT_SCENE_DEFINE_ZH
)

RESPONSE_FORMAT_SIMPLE = """
{
    "thoughts": "thoughts summary to say to user",
    "direct_response": "If the context is sufficient to answer user, reply directly without sql. If information is insufficient, provide detailed guidance on what is needed",
    "sql": "SQL Query to run",
    "display_type": "Data display method",
    "missing_info": "If unable to generate SQL, list specific missing information and suggestions",
    "analysis_report": {
        "summary": "Brief summary of the analysis results (optional, only when user requests analysis or report)",
        "key_findings": [
            "Key finding 1",
            "Key finding 2"
        ],
        "insights": [
            "Business insight 1",
            "Business insight 2"
        ],
        "recommendations": [
            "Recommendation 1",
            "Recommendation 2"
        ],
        "methodology": "Explanation of analysis approach and methods used"
    }
}
"""


# Temperature is a configuration hyperparameter that controls the randomness of
# language model output.
# A high temperature produces more unpredictable and creative results, while a low
# temperature produces more common and conservative output.
# For example, if you adjust the temperature to 0.5, the model will usually generate
# text that is more predictable and less creative than if you set the temperature to
# 1.0.
PROMPT_TEMPERATURE = 0.5

prompt = ChatPromptTemplate(
    messages=[
        SystemPromptTemplate.from_template(
            _DEFAULT_TEMPLATE,
            response_format=json.dumps(
                RESPONSE_FORMAT_SIMPLE, ensure_ascii=False, indent=4
            ),
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanPromptTemplate.from_template("{user_input}"),
    ]
)

prompt_adapter = AppScenePromptTemplateAdapter(
    prompt=prompt,
    template_scene=ChatScene.ChatWithDbExecute.value(),
    stream_out=True,
    output_parser=DbChatOutputParser(),
    temperature=PROMPT_TEMPERATURE,
)
CFG.prompt_template_registry.register(prompt_adapter, is_default=True)

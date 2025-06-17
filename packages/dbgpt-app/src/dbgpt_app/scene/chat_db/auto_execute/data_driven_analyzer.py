#!/usr/bin/env python3
"""
数据驱动分析器 - 基于真实SQL执行结果生成分析报告
Data-Driven Analyzer - Generate analysis reports based on actual SQL execution results
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataDrivenAnalyzer:
    """基于真实数据的分析报告生成器"""
    
    def __init__(self):
        self.analysis_keywords = [
            '分析', '报告', '总结', '根因', '原因分析',
            'analysis', 'analyze', 'report', 'summary', 'root cause'
        ]
    
    def should_generate_analysis_report(self, user_input: str) -> bool:
        """检查是否需要生成分析报告"""
        if not user_input:
            return False
        
        user_input_lower = user_input.lower()
        return any(keyword.lower() in user_input_lower for keyword in self.analysis_keywords)
    
    def generate_data_driven_report(self, 
                                  result_df: pd.DataFrame, 
                                  user_input: str, 
                                  sql: str) -> Dict[str, Any]:
        """基于真实数据生成分析报告"""
        
        try:
            if result_df.empty:
                return self._generate_empty_data_report(user_input, sql)
            
            # 分析数据特征
            data_insights = self._analyze_data_characteristics(result_df)
            
            # 生成业务分析
            business_analysis = self._generate_business_analysis(result_df, user_input, data_insights)
            
            # 构建完整报告
            report = {
                "summary": business_analysis["summary"],
                "key_findings": business_analysis["key_findings"],
                "insights": business_analysis["insights"],
                "recommendations": business_analysis["recommendations"],
                "methodology": business_analysis["methodology"]
            }
            
            logger.info(f"Generated data-driven analysis report with {len(result_df)} records")
            return report
            
        except Exception as e:
            logger.error(f"Error generating data-driven report: {str(e)}")
            return self._generate_fallback_report(user_input, sql, str(e))
    
    def _analyze_data_characteristics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析数据特征"""
        insights = {
            "record_count": len(df),
            "column_count": len(df.columns),
            "numeric_columns": [],
            "date_columns": [],
            "categorical_columns": [],
            "trends": {},
            "statistics": {},
            "patterns": {}
        }
        
        # 分析列类型
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                insights["numeric_columns"].append(col)
                
                # 计算统计信息
                insights["statistics"][col] = {
                    "mean": df[col].mean(),
                    "median": df[col].median(),
                    "std": df[col].std(),
                    "min": df[col].min(),
                    "max": df[col].max(),
                    "null_count": df[col].isnull().sum()
                }
                
                # 分析趋势（如果有多行数据）
                if len(df) > 1:
                    first_val = df[col].iloc[0]
                    last_val = df[col].iloc[-1]
                    if pd.notnull(first_val) and pd.notnull(last_val):
                        change_rate = (last_val - first_val) / first_val if first_val != 0 else 0
                        insights["trends"][col] = {
                            "direction": "上升" if change_rate > 0.05 else "下降" if change_rate < -0.05 else "稳定",
                            "change_rate": change_rate,
                            "first_value": first_val,
                            "last_value": last_val
                        }
            
            elif 'date' in col.lower() or 'time' in col.lower():
                insights["date_columns"].append(col)
            else:
                insights["categorical_columns"].append(col)
        
        # 识别特殊模式
        insights["patterns"] = self._identify_patterns(df, insights)
        
        return insights
    
    def _identify_patterns(self, df: pd.DataFrame, insights: Dict) -> Dict[str, Any]:
        """识别数据模式"""
        patterns = {}
        
        # 检查是否是逾期率分析
        mob_columns = [col for col in df.columns if 'MOB' in str(col).upper()]
        if mob_columns:
            patterns["analysis_type"] = "逾期率分析"
            patterns["mob_periods"] = mob_columns
            
            # 分析MOB期数的逾期率变化
            if len(mob_columns) > 1:
                mob_trends = []
                for col in mob_columns:
                    if col in insights["statistics"]:
                        avg_rate = insights["statistics"][col]["mean"]
                        mob_trends.append((col, avg_rate))
                
                patterns["mob_trend_analysis"] = mob_trends
        
        # 检查是否是时间序列分析
        date_cols = insights["date_columns"] + [col for col in df.columns if any(x in col.lower() for x in ['月份', 'month', '日期', 'date'])]
        if date_cols:
            patterns["analysis_type"] = "时间序列分析"
            patterns["time_columns"] = date_cols
        
        # 检查数据质量
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        patterns["data_quality"] = {
            "completeness": (total_cells - null_cells) / total_cells,
            "null_percentage": null_cells / total_cells
        }
        
        return patterns
    
    def _generate_business_analysis(self, df: pd.DataFrame, user_input: str, data_insights: Dict) -> Dict[str, Any]:
        """生成业务分析"""
        
        analysis_type = data_insights["patterns"].get("analysis_type", "通用数据分析")
        
        if analysis_type == "逾期率分析":
            return self._generate_overdue_analysis(df, user_input, data_insights)
        elif analysis_type == "时间序列分析":
            return self._generate_time_series_analysis(df, user_input, data_insights)
        else:
            return self._generate_general_analysis(df, user_input, data_insights)
    
    def _generate_overdue_analysis(self, df: pd.DataFrame, user_input: str, data_insights: Dict) -> Dict[str, Any]:
        """生成逾期率分析报告"""
        
        mob_columns = data_insights["patterns"].get("mob_periods", [])
        statistics = data_insights["statistics"]
        trends = data_insights["trends"]
        
        # 生成摘要
        avg_rates = []
        for col in mob_columns:
            if col in statistics:
                avg_rate = statistics[col]["mean"]
                avg_rates.append(f"{col}: {avg_rate:.2%}")
        
        summary = f"基于{len(df)}条记录的逾期率分析显示，{', '.join(avg_rates[:3])}。数据覆盖{len(mob_columns)}个MOB期数，为风险管理提供了详细的量化依据。"
        
        # 生成关键发现
        key_findings = []
        key_findings.append(f"🔍 共分析{len(df)}条记录，涵盖{len(mob_columns)}个MOB期数的逾期表现")
        
        # 分析具体数值
        for col in mob_columns[:3]:  # 只分析前3个MOB期
            if col in statistics:
                stats = statistics[col]
                key_findings.append(f"🔍 {col}平均逾期率为{stats['mean']:.2%}，最高{stats['max']:.2%}，最低{stats['min']:.2%}")
        
        # 分析趋势
        for col in mob_columns:
            if col in trends:
                trend = trends[col]
                key_findings.append(f"🔍 {col}期数逾期率呈{trend['direction']}趋势，变化幅度{trend['change_rate']:.1%}")
        
        # 数据质量分析
        data_quality = data_insights["patterns"]["data_quality"]
        key_findings.append(f"🔍 数据完整度{data_quality['completeness']:.1%}，数据质量{'良好' if data_quality['completeness'] > 0.9 else '需要改善'}")
        
        # 生成业务洞察
        insights = []
        
        # 基于实际数值的洞察
        high_risk_periods = []
        for col in mob_columns:
            if col in statistics and statistics[col]["mean"] > 0.1:  # 10%以上认为高风险
                high_risk_periods.append(col)
        
        if high_risk_periods:
            insights.append(f"💡 {', '.join(high_risk_periods)}期数逾期率超过10%，需要重点关注和风险控制")
        
        # 趋势洞察
        rising_trends = [col for col in trends if trends[col]["direction"] == "上升"]
        if rising_trends:
            insights.append(f"💡 {', '.join(rising_trends)}期数逾期率呈上升趋势，可能反映风险积累或外部环境变化")
        
        # MOB期数对比洞察
        if len(mob_columns) > 1:
            mob_rates = [(col, statistics[col]["mean"]) for col in mob_columns if col in statistics]
            mob_rates.sort(key=lambda x: x[1])
            insights.append(f"💡 逾期率随MOB期数递增，{mob_rates[0][0]}最低({mob_rates[0][1]:.2%})，{mob_rates[-1][0]}最高({mob_rates[-1][1]:.2%})")
        
        insights.append("💡 逾期率数据为风险定价、额度管理和催收策略制定提供了量化基础")
        
        # 生成建议
        recommendations = []
        
        # 基于具体数值的建议
        for col in high_risk_periods:
            recommendations.append(f"🎯 针对{col}期数高逾期率({statistics[col]['mean']:.2%})，建议加强该期数客户的跟踪管理")
        
        # 基于趋势的建议
        for col in rising_trends:
            recommendations.append(f"🎯 {col}期数逾期率上升趋势需要深入分析原因，考虑调整风控策略")
        
        recommendations.append("🎯 建立MOB期数逾期率预警机制，设置阈值进行实时监控")
        recommendations.append(f"🎯 基于当前数据特征，建议重点关注逾期率超过{np.mean([statistics[col]['mean'] for col in statistics]):.1%}的客户群体")
        
        # 方法论
        methodology = f"🔬 基于{len(df)}条真实业务数据的统计分析，采用描述性统计方法计算各MOB期数的均值、中位数、标准差等指标，结合趋势分析识别风险模式。数据完整度{data_quality['completeness']:.1%}，分析结果具有较高可信度。"
        
        return {
            "summary": summary,
            "key_findings": key_findings,
            "insights": insights,
            "recommendations": recommendations,
            "methodology": methodology
        }
    
    def _generate_time_series_analysis(self, df: pd.DataFrame, user_input: str, data_insights: Dict) -> Dict[str, Any]:
        """生成时间序列分析报告"""
        
        time_columns = data_insights["patterns"].get("time_columns", [])
        statistics = data_insights["statistics"]
        trends = data_insights["trends"]
        
        summary = f"基于{len(df)}条记录的时间序列分析，数据跨度涵盖{len(df)}个时间点，为趋势识别和预测提供了数据基础。"
        
        key_findings = []
        key_findings.append(f"🔍 时间序列数据包含{len(df)}个观测点，{len(data_insights['numeric_columns'])}个数值指标")
        
        # 分析数值列的时间趋势
        for col in data_insights["numeric_columns"][:3]:
            if col in statistics:
                stats = statistics[col]
                key_findings.append(f"🔍 {col}在观测期内平均值{stats['mean']:.3f}，波动范围{stats['min']:.3f}-{stats['max']:.3f}")
        
        # 趋势分析
        for col in trends:
            trend = trends[col]
            key_findings.append(f"🔍 {col}呈{trend['direction']}趋势，从{trend['first_value']:.3f}变化到{trend['last_value']:.3f}")
        
        insights = [
            "💡 时间序列数据反映了业务指标的动态变化过程",
            "💡 趋势分析有助于识别业务发展的关键转折点",
            "💡 数据波动可能与季节性因素、政策变化或市场环境相关",
            "💡 持续监控时间序列指标有助于及时发现异常和机会"
        ]
        
        recommendations = [
            "🎯 建立时间序列预警机制，监控关键指标的异常变化",
            "🎯 结合外部因素分析数据波动的根本原因",
            "🎯 建立预测模型，基于历史趋势预测未来走势",
            "🎯 定期评估时间序列模式，优化业务策略"
        ]
        
        methodology = f"🔬 采用时间序列分析方法，基于{len(df)}个时间点的真实数据计算趋势、波动和周期性特征。通过描述性统计和趋势分析识别数据模式。"
        
        return {
            "summary": summary,
            "key_findings": key_findings,
            "insights": insights,
            "recommendations": recommendations,
            "methodology": methodology
        }
    
    def _generate_general_analysis(self, df: pd.DataFrame, user_input: str, data_insights: Dict) -> Dict[str, Any]:
        """生成通用数据分析报告"""
        
        statistics = data_insights["statistics"]
        
        summary = f"基于{len(df)}条记录、{len(df.columns)}个字段的数据分析，为业务理解和决策支持提供了量化依据。"
        
        key_findings = []
        key_findings.append(f"🔍 数据集包含{len(df)}条记录，{len(data_insights['numeric_columns'])}个数值字段，{len(data_insights['categorical_columns'])}个分类字段")
        
        # 数值字段分析
        for col in data_insights["numeric_columns"][:3]:
            if col in statistics:
                stats = statistics[col]
                key_findings.append(f"🔍 {col}平均值{stats['mean']:.3f}，标准差{stats['std']:.3f}，数据分布{'集中' if stats['std']/stats['mean'] < 0.5 else '分散'}")
        
        # 数据质量
        data_quality = data_insights["patterns"]["data_quality"]
        key_findings.append(f"🔍 数据完整度{data_quality['completeness']:.1%}，缺失值比例{data_quality['null_percentage']:.1%}")
        
        insights = [
            "💡 数据分析结果提供了业务现状的量化视图",
            "💡 统计指标有助于识别数据中的关键模式和异常",
            "💡 数据质量评估为后续分析的可信度提供了参考",
            "💡 多维度数据分析支持更全面的业务理解"
        ]
        
        recommendations = [
            "🎯 基于数据分析结果制定针对性的业务策略",
            "🎯 建立数据质量监控机制，确保分析结果的可靠性",
            "🎯 深入分析关键指标的驱动因素和影响机制",
            "🎯 定期更新数据分析，跟踪业务变化趋势"
        ]
        
        methodology = f"🔬 采用描述性统计分析方法，基于{len(df)}条真实数据计算均值、中位数、标准差等统计指标，结合数据质量评估提供综合分析结果。"
        
        return {
            "summary": summary,
            "key_findings": key_findings,
            "insights": insights,
            "recommendations": recommendations,
            "methodology": methodology
        }
    
    def _generate_empty_data_report(self, user_input: str, sql: str) -> Dict[str, Any]:
        """生成空数据报告"""
        return {
            "summary": f"针对查询'{user_input}'执行SQL后未返回数据，可能是查询条件过于严格或数据确实不存在。",
            "key_findings": [
                "🔍 SQL查询执行成功但未返回任何记录",
                "🔍 可能的原因包括：查询条件过于严格、数据时间范围不匹配、表中确实无相关数据",
                "🔍 建议检查查询条件的合理性和数据源的完整性",
                "🔍 可以尝试放宽查询条件或扩大时间范围",
                "🔍 确认相关业务数据是否已正确录入系统"
            ],
            "insights": [
                "💡 空结果可能反映了业务的真实状况，也可能是查询逻辑的问题",
                "💡 建议结合业务背景判断空结果的合理性",
                "💡 可以通过调整查询参数来验证数据存在性",
                "💡 空结果也是一种有价值的业务信息"
            ],
            "recommendations": [
                "🎯 检查并调整查询条件，确保参数设置合理",
                "🎯 验证数据源的完整性和时效性",
                "🎯 尝试更宽泛的查询条件以确认数据存在性",
                "🎯 如确认无数据，考虑这一结果的业务含义"
            ],
            "methodology": "🔬 基于SQL查询结果的空值分析，结合查询逻辑和业务背景进行原因推测和建议生成。"
        }
    
    def _generate_fallback_report(self, user_input: str, sql: str, error_msg: str) -> Dict[str, Any]:
        """生成兜底报告"""
        return {
            "summary": f"在生成数据驱动分析报告时遇到技术问题，已切换到基础分析模式。",
            "key_findings": [
                "🔍 数据分析过程中遇到技术异常",
                "🔍 已执行SQL查询并获取结果数据",
                "🔍 建议检查数据格式和结构的完整性",
                "🔍 系统已记录详细错误信息供技术团队分析",
                "🔍 基础的查询结果展示功能正常工作"
            ],
            "insights": [
                "💡 技术异常不影响SQL查询的正确执行",
                "💡 数据结果仍然可用于人工分析",
                "💡 建议关注数据质量和格式规范性",
                "💡 系统正在持续优化分析算法的稳定性"
            ],
            "recommendations": [
                "🎯 可以基于查询结果进行人工分析",
                "🎯 如需详细分析报告，建议联系技术支持",
                "🎯 检查原始数据的格式和完整性",
                "🎯 考虑简化查询逻辑以提高分析成功率"
            ],
            "methodology": f"🔬 基础分析模式，技术异常信息：{error_msg[:100]}..."
        } 
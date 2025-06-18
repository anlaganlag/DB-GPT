"""
应用SQL响应修复补丁到out_parser.py
"""

import os
import shutil
from datetime import datetime

def backup_original_file():
    """备份原始文件"""
    source = "/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/out_parser.py"
    backup = f"/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/out_parser.py.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if os.path.exists(source):
        shutil.copy2(source, backup)
        print(f"✅ 原始文件已备份到: {backup}")
        return True
    return False

def apply_patch():
    """应用修复补丁"""
    target_file = "/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/out_parser.py"
    
    # 读取原始文件
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经应用过补丁
    if "SQLResponseFixer" in content:
        print("⚠️ 补丁已经应用过，跳过")
        return True
    
    # 添加导入语句
    import_patch = """
# === SQL响应修复器补丁 ===
import sys
import os
sys.path.append('/app')

try:
    from enhanced_out_parser_fix import SQLResponseFixer
    _sql_response_fixer = SQLResponseFixer()
    logger.info("SQL响应修复器已加载")
except ImportError as e:
    logger.warning(f"无法加载SQL响应修复器: {e}")
    _sql_response_fixer = None
"""
    
    # 在导入部分后添加
    import_pos = content.find("logger = logging.getLogger(__name__)")
    if import_pos != -1:
        content = content[:import_pos] + import_patch + "\n" + content[import_pos:]
    
    # 修改parse_prompt_response方法
    method_start = content.find("def parse_prompt_response(self, model_out_text, user_input: str = \"\"):")
    if method_start != -1:
        # 找到方法结束位置
        method_lines = content[method_start:].split('\n')
        indent_level = len(method_lines[0]) - len(method_lines[0].lstrip())
        
        # 找到方法结束
        method_end = method_start
        for i, line in enumerate(method_lines[1:], 1):
            if line.strip() and len(line) - len(line.lstrip()) <= indent_level and not line.lstrip().startswith('#'):
                method_end = method_start + len('\n'.join(method_lines[:i]))
                break
        
        # 在方法末尾添加修复逻辑
        fix_code = """
        
        # === SQL响应修复补丁 ===
        if _sql_response_fixer and isinstance(result, dict):
            try:
                result = _sql_response_fixer.fix_response(result, user_input)
                logger.info("SQL响应已通过修复器处理")
            except Exception as e:
                logger.error(f"SQL响应修复失败: {e}")
        # === 补丁结束 ===
        
        return result"""
        
        # 找到return语句并替换
        return_pos = content.rfind("return result", method_start, method_end)
        if return_pos != -1:
            content = content[:return_pos] + fix_code[8:]  # 移除开头的换行
        else:
            # 如果找不到return，在方法末尾添加
            content = content[:method_end] + fix_code + content[method_end:]
    
    # 写入修改后的文件
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 修复补丁已应用到out_parser.py")
    return True

if __name__ == "__main__":
    print("🔧 开始应用SQL响应修复补丁...")
    
    if backup_original_file():
        if apply_patch():
            print("🎉 修复补丁应用成功！")
        else:
            print("❌ 修复补丁应用失败")
    else:
        print("❌ 无法备份原始文件")

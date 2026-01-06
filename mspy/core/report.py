"""
报告生成模块

从 packages/core/src/utils.ts 迁移
保留HTML报告生成功能
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from mspy.shared.common import get_midscene_run_sub_dir
from mspy.shared.logger import get_debug
from mspy.shared.utils import replace_illegal_path_chars


_debug = get_debug("report")

# 报告文件扩展名
GROUPED_ACTION_DUMP_FILE_EXT = ".json"


def get_version() -> str:
    """获取SDK版本"""
    # 使用直接导入避免循环引用
    try:
        import importlib.metadata
        return importlib.metadata.version("mspy")
    except Exception:
        return "0.1.0"  # 默认版本


def get_report_file_name(base_name: str) -> str:
    """
    获取报告文件名
    
    Args:
        base_name: 基础名称
    
    Returns:
        处理后的文件名
    """
    safe_name = replace_illegal_path_chars(base_name)
    timestamp = int(time.time() * 1000)
    return f"{safe_name}-{timestamp}"


def stringify_dump_data(dump: Any) -> str:
    """
    将dump数据序列化为JSON字符串
    
    Args:
        dump: Dump数据对象
    
    Returns:
        JSON字符串
    """
    def convert(obj: Any) -> Any:
        if hasattr(obj, '__dataclass_fields__'):
            # 是dataclass
            return {k: convert(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(item) for item in obj]
        elif isinstance(obj, Exception):
            return str(obj)
        return obj
    
    return json.dumps(convert(dump), ensure_ascii=False, indent=2)


def write_log_file(
    file_name: str,
    file_ext: str,
    file_content: str,
    file_type: str = "dump",
    generate_report: bool = True,
) -> Optional[str]:
    """
    写入日志文件
    
    Args:
        file_name: 文件名
        file_ext: 文件扩展名
        file_content: 文件内容
        file_type: 文件类型
        generate_report: 是否生成报告
    
    Returns:
        文件路径或None
    """
    if not generate_report:
        return None
    
    try:
        # 获取dump目录
        dump_dir = get_midscene_run_sub_dir("dump")
        
        # 构建文件路径
        full_name = f"{file_name}{file_ext}"
        file_path = Path(dump_dir) / full_name
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        
        _debug(f"Wrote {file_type} file: {file_path}")
        return str(file_path)
        
    except Exception as e:
        _debug(f"Failed to write {file_type} file: {e}")
        return None


def report_html_content(dump_json: str) -> str:
    """
    生成报告HTML内容
    
    Args:
        dump_json: Dump数据的JSON字符串
    
    Returns:
        HTML内容
    """
    # 转义JSON用于嵌入HTML
    escaped_json = (
        dump_json
        .replace("\\", "\\\\")
        .replace("</", "<\\/")
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Midscene Report</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #007bff;
        }}
        .group {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            overflow: hidden;
        }}
        .group-header {{
            background: #007bff;
            color: white;
            padding: 15px 20px;
        }}
        .group-header h2 {{
            font-size: 18px;
            font-weight: 500;
        }}
        .execution {{
            border-bottom: 1px solid #eee;
            padding: 15px 20px;
        }}
        .execution:last-child {{
            border-bottom: none;
        }}
        .execution-name {{
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
        }}
        .task {{
            background: #f8f9fa;
            border-radius: 4px;
            padding: 10px 15px;
            margin: 5px 0;
        }}
        .task-type {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .task-status {{
            font-size: 12px;
            padding: 2px 8px;
            border-radius: 3px;
            margin-left: 10px;
        }}
        .status-finished {{
            background: #d4edda;
            color: #155724;
        }}
        .status-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        .status-pending {{
            background: #fff3cd;
            color: #856404;
        }}
        .task-param {{
            font-size: 14px;
            color: #495057;
            margin-top: 5px;
        }}
        .screenshot {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 10px;
        }}
        .meta {{
            font-size: 12px;
            color: #999;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Midscene Report</h1>
        <div id="report-content"></div>
        <div class="meta">
            Generated by Midscene Python SDK
        </div>
    </div>
    <script>
        const data = {escaped_json};
        const dumpData = typeof data === 'string' ? JSON.parse(data) : data;
        
        function renderReport(dump) {{
            const container = document.getElementById('report-content');
            
            // 渲染组
            const groupHtml = `
                <div class="group">
                    <div class="group-header">
                        <h2>${{dump.groupName || 'Midscene Report'}}</h2>
                        ${{dump.groupDescription ? `<p>${{dump.groupDescription}}</p>` : ''}}
                    </div>
                    ${{(dump.executions || []).map(exec => `
                        <div class="execution">
                            <div class="execution-name">${{exec.name || 'Execution'}}</div>
                            ${{(exec.tasks || []).map(task => `
                                <div class="task">
                                    <span class="task-type">${{task.type || 'Task'}}</span>
                                    <span class="task-status status-${{task.status || 'pending'}}">${{task.status || 'pending'}}</span>
                                    ${{task.param ? `<div class="task-param">${{JSON.stringify(task.param)}}</div>` : ''}}
                                    ${{task.errorMessage ? `<div class="task-param" style="color: red;">${{task.errorMessage}}</div>` : ''}}
                                </div>
                            `).join('')}}
                        </div>
                    `).join('')}}
                </div>
            `;
            
            container.innerHTML = groupHtml;
        }}
        
        renderReport(dumpData);
    </script>
</body>
</html>
"""


def write_report_html(
    dump_json: str,
    file_name: str,
) -> Optional[str]:
    """
    生成并写入HTML报告
    
    Args:
        dump_json: Dump数据的JSON字符串
        file_name: 文件名
    
    Returns:
        文件路径或None
    """
    try:
        # 获取report目录
        report_dir = get_midscene_run_sub_dir("report")
        
        # 构建文件路径
        file_path = Path(report_dir) / f"{file_name}.html"
        
        # 生成HTML内容
        html_content = report_html_content(dump_json)
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        _debug(f"Wrote report file: {file_path}")
        return str(file_path)
        
    except Exception as e:
        _debug(f"Failed to write report file: {e}")
        return None


def print_report_msg(report_file: str) -> None:
    """
    打印报告消息
    
    Args:
        report_file: 报告文件路径
    """
    print(f"\n📊 Midscene report: {report_file}\n")

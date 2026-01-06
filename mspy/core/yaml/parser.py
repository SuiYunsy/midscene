"""
YAML脚本解析器

从 packages/core/src/yaml/builder.ts 和 utils.ts 迁移
"""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import yaml


@dataclass
class YamlFlowItem:
    """YAML流程项"""
    ai_act: Optional[str] = None
    ai_assert: Optional[str] = None
    ai_query: Optional[dict[str, Any]] = None
    ai_wait_for: Optional[str] = None
    sleep: Optional[int] = None
    
    # 动作参数
    ai_tap: Optional[str] = None
    ai_hover: Optional[str] = None
    ai_input: Optional[dict[str, Any]] = None
    ai_keyboard_press: Optional[dict[str, Any]] = None
    ai_scroll: Optional[dict[str, Any]] = None


@dataclass
class YamlTask:
    """YAML任务"""
    name: str
    flow: list[YamlFlowItem] = field(default_factory=list)
    

@dataclass
class MidsceneYamlScript:
    """Midscene YAML脚本"""
    tasks: list[YamlTask] = field(default_factory=list)
    target: Optional[dict[str, Any]] = None
    web: Optional[dict[str, Any]] = None
    android: Optional[dict[str, Any]] = None
    ios: Optional[dict[str, Any]] = None


def parse_yaml_script(
    content: str,
    file_type: Literal["yaml", "json"] = "yaml"
) -> MidsceneYamlScript:
    """
    解析YAML脚本
    
    Args:
        content: YAML内容
        file_type: 文件类型
    
    Returns:
        MidsceneYamlScript实例
    """
    if file_type == "json":
        import json
        data = json.loads(content)
    else:
        data = yaml.safe_load(content)
    
    if not data:
        raise ValueError("Empty YAML content")
    
    # 解析任务
    tasks = []
    raw_tasks = data.get("tasks", [])
    
    for raw_task in raw_tasks:
        task_name = raw_task.get("name", "Unnamed Task")
        
        # 解析流程
        flow_items = []
        raw_flow = raw_task.get("flow", [])
        
        for raw_item in raw_flow:
            flow_item = YamlFlowItem(
                ai_act=raw_item.get("aiAct") or raw_item.get("ai_act"),
                ai_assert=raw_item.get("aiAssert") or raw_item.get("ai_assert"),
                ai_query=raw_item.get("aiQuery") or raw_item.get("ai_query"),
                ai_wait_for=raw_item.get("aiWaitFor") or raw_item.get("ai_wait_for"),
                sleep=raw_item.get("sleep"),
                ai_tap=raw_item.get("aiTap") or raw_item.get("ai_tap"),
                ai_hover=raw_item.get("aiHover") or raw_item.get("ai_hover"),
                ai_input=raw_item.get("aiInput") or raw_item.get("ai_input"),
                ai_keyboard_press=raw_item.get("aiKeyboardPress") or raw_item.get("ai_keyboard_press"),
                ai_scroll=raw_item.get("aiScroll") or raw_item.get("ai_scroll"),
            )
            flow_items.append(flow_item)
        
        tasks.append(YamlTask(name=task_name, flow=flow_items))
    
    return MidsceneYamlScript(
        tasks=tasks,
        target=data.get("target"),
        web=data.get("web"),
        android=data.get("android"),
        ios=data.get("ios"),
    )


def build_detailed_locate_param(
    prompt: str,
    options: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    构建详细定位参数
    
    Args:
        prompt: 定位提示
        options: 额外选项
    
    Returns:
        详细定位参数字典
    """
    result = {"prompt": prompt}
    
    if options:
        if options.get("deep_think") or options.get("deepThink"):
            result["deepThink"] = True
        
        if "index" in options:
            result["index"] = options["index"]
    
    return result

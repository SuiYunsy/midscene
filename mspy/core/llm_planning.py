# -*- coding: utf-8 -*-
"""
Midscene LLM Planning Module
LLM规划模块，负责生成动作计划
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ..shared import (
    get_logger,
    ModelConfig,
    PlanningAction,
    PlanningAIResponse,
    AIUsageInfo,
    UIContext,
    assert_condition,
)
from .conversation_history import ConversationHistory
from .service_caller import call_ai_with_object_response
from .common import (
    fill_bbox_param,
    build_yaml_flow_from_plans,
)

logger = get_logger("planning")


def _bbox_description() -> str:
    """返回bbox描述，针对qwen3-vl"""
    return "2d bounding box as [xmin, ymin, xmax, ymax] normalized to 0-1000"


def _vl_locate_param_with_bbox() -> str:
    """返回带bbox的locate参数描述"""
    return f"{{bbox: [number, number, number, number], prompt: string }} // {_bbox_description()}"


def _description_for_action(action: Dict[str, Any]) -> str:
    """
    生成单个action的描述
    
    Args:
        action: 动作定义
    
    Returns:
        动作描述字符串
    """
    tab = "  "
    fields = []
    
    name = action.get("name", "")
    description = action.get("description", "No description provided")
    param_schema = action.get("param_schema", {})
    
    # 添加type字段
    fields.append(f'- type: "{name}"')
    
    # 处理参数
    if param_schema:
        param_lines = []
        for key, field_info in param_schema.items():
            field_type = field_info.get("type", "any")
            field_desc = field_info.get("description", "")
            is_optional = field_info.get("optional", False)
            is_locator = field_info.get("is_locator", False)
            
            key_str = f"{key}?" if is_optional else key
            
            if is_locator:
                # 使用带bbox的locate参数描述
                type_str = _vl_locate_param_with_bbox()
            else:
                type_str = field_type
            
            param_line = f"{key_str}: {type_str}"
            if field_desc:
                param_line += f" // {field_desc}"
            param_lines.append(param_line)
        
        if param_lines:
            fields.append("- param:")
            for line in param_lines:
                fields.append(f"  - {line}")
    
    fields_str = "\n".join([tab + f for f in fields])
    return f"""- {name}, {description}
{tab}{fields_str}""".strip()


def _build_system_prompt(action_space: List[Dict[str, Any]]) -> str:
    """
    构建系统提示词
    
    Args:
        action_space: 可用动作列表
    
    Returns:
        系统提示词
    """
    action_descriptions = [_description_for_action(action) for action in action_space]
    action_list = "\n".join(action_descriptions)
    
    log_field_instruction = """
## About the `log` field (preamble message)

The `log` field is a brief preamble message to the user explaining what you're about to do. It should follow these principles and examples:

- **Use the same language as the user's instruction**
- **Keep it concise**: be no more than 1-2 sentences, focused on immediate, tangible next steps. (8–12 words or Chinese characters for quick updates).
- **Build on prior context**: if this is not the first action to be done, use the preamble message to connect the dots with what's been done so far and create a sense of momentum and clarity for the user to understand your next actions.
- **Keep your tone light, friendly and curious**: add small touches of personality in preambles feel collaborative and engaging.

**Examples:**
- "Click the login button"
- "Scroll to find the 'Yes' button in popup"
- "Previous actions failed to find the 'Yes' button, i will try again"
- "Go back to find the login button"
"""

    common_output_fields = '''"error"?: string, // Error messages about unexpected situations, if any. Only think it is an error when the situation is not foreseeable according to the instruction. Use the same language as the user's instruction.
  "more_actions_needed_by_instruction": boolean, // Consider if there is still more action(s) to do after the action in "Log" is done, according to the instruction. If so, set this field to true. Otherwise, set it to false.'''

    return f"""
Target: User will give you an instruction, some screenshots and previous logs indicating what have been done. Your task is to plan the next one action according to current situation to accomplish the instruction.

Please tell what the next one action is (or null if no action should be done) to do the tasks the instruction requires. 

## Rules

- Don't give extra actions or plans beyond the instruction. For example, don't try to submit the form if the instruction is only to fill something.
- Give just the next ONE action you should do
- Consider the current screenshot and give the action that is most likely to accomplish the instruction. For example, if the next step is to click a button but it's not visible in the screenshot, you should try to find it first instead of give a click action.
- Make sure the previous actions are completed successfully before performing the next step
- If there are some error messages reported by the previous actions, don't give up, try parse a new action to recover. If the error persists for more than 5 times, you should think this is an error and set the "error" field to the error message.
- If there is nothing to do but waiting, set the "sleep" field to the positive waiting time in milliseconds and null for the "action" field.
- Assertions are also important steps. When getting the assertion instruction, a solid conclusion is required. You should explicitly state your conclusion by calling the "Print_Assert_Result" action.

## Supporting actions
{action_list}

{log_field_instruction}

## Return format

Return in JSON format:
{{
  "log": string, // a brief preamble to the user explaining what you're about to do
  {common_output_fields}
  "action": 
    {{
      "type": string, // the type of the action
      "param"?: {{ // The parameter of the action, if any
         // k-v style parameter fields
      }}, 
    }} | null,
  ,
  "sleep"?: number, // The sleep time after the action, in milliseconds.
}}

For example, if the instruction is to login and the form has already been filled, this is a valid return value:

{{
  "log": "Click the login button",
  "more_actions_needed_by_instruction": false,
  "action": {{
    "type": "Tap",
    "param": {{
      "locate": {{ 
        "prompt": "The login button", "bbox": [100, 200, 300, 400]
      }}
    }}
  }}
}}
"""


async def plan(
    user_instruction: str,
    context: UIContext,
    action_space: List[Dict[str, Any]],
    model_config: ModelConfig,
    conversation_history: ConversationHistory,
    action_context: Optional[str] = None,
    images_include_count: Optional[int] = 2,
) -> PlanningAIResponse:
    """
    生成动作计划
    
    Args:
        user_instruction: 用户指令
        context: UI上下文
        action_space: 可用动作空间
        model_config: 模型配置
        conversation_history: 对话历史
        action_context: 额外的动作上下文
        images_include_count: 要包含的图像数量
    
    Returns:
        PlanningAIResponse
    """
    screenshot_base64 = context.screenshot_base64
    size = context.size
    
    system_prompt = _build_system_prompt(action_space)
    
    image_payload = screenshot_base64
    image_width = size.width
    image_height = size.height
    right_limit = image_width
    bottom_limit = image_height
    
    action_context_str = ""
    if action_context:
        action_context_str = f"<high_priority_knowledge>{action_context}</high_priority_knowledge>\n"
    
    instruction = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{action_context_str}<user_instruction>{user_instruction}</user_instruction>",
                },
            ],
        }
    ]
    
    # 构建最新的反馈消息
    if conversation_history.pending_feedback_message:
        latest_feedback_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{conversation_history.pending_feedback_message}. The last screenshot is attached. Please going on according to the instruction.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_payload,
                        "detail": "high",
                    },
                },
            ],
        }
        conversation_history.reset_pending_feedback_message_if_exists()
    else:
        latest_feedback_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "this is the latest screenshot",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_payload,
                        "detail": "high",
                    },
                },
            ],
        }
    
    conversation_history.append(latest_feedback_message)
    history_log = conversation_history.snapshot(images_include_count)
    
    messages = [
        {"role": "system", "content": system_prompt},
        *instruction,
        *history_log,
    ]
    
    # 调用AI
    result = await call_ai_with_object_response(messages, model_config)
    
    plan_from_ai = result["content"]
    raw_response = result["contentString"]
    usage = result["usage"]
    
    # 解析响应
    action = plan_from_ai.get("action")
    actions = [action] if action else []
    
    # 处理定位参数中的bbox
    vl_mode = model_config.vl_mode
    for action_item in actions:
        if action_item:
            action_type = action_item.get("type")
            param = action_item.get("param", {})
            
            # 查找并处理locate字段
            for key, value in param.items():
                if isinstance(value, dict) and "bbox" in value:
                    param[key] = fill_bbox_param(
                        value,
                        image_width,
                        image_height,
                        right_limit,
                        bottom_limit,
                        vl_mode,
                    )
    
    # 构建响应
    planning_actions = []
    for action_item in actions:
        if action_item:
            planning_actions.append(PlanningAction(
                type=action_item.get("type", ""),
                param=action_item.get("param", {}),
                thought=plan_from_ai.get("log"),
            ))
    
    response = PlanningAIResponse(
        actions=planning_actions,
        more_actions_needed_by_instruction=plan_from_ai.get("more_actions_needed_by_instruction", False),
        log=plan_from_ai.get("log", ""),
        sleep=plan_from_ai.get("sleep"),
        error=plan_from_ai.get("error"),
        usage=usage,
        raw_response=raw_response,
    )
    
    # 添加响应到对话历史
    conversation_history.append({
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": raw_response,
            },
        ],
    })
    
    return response

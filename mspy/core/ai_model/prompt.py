"""
LLM规划提示词模块
"""

from typing import Any, Dict, List, Optional
from ...shared import get_debug, DeviceAction

debug = get_debug('prompt:planning')


def bbox_description() -> str:
    """
    获取bbox描述（用于qwen3-vl模式）
    """
    return '2d bounding box as [xmin, ymin, xmax, ymax]'


def get_vl_locate_param() -> str:
    """
    获取VL模式的定位参数描述
    """
    return f'{{bbox: [number, number, number, number], prompt: string }} // {bbox_description()}'


def description_for_action(action: DeviceAction, locator_schema_type_description: str) -> str:
    """
    为动作生成描述
    
    Args:
        action: 设备动作
        locator_schema_type_description: 定位器schema类型描述
    
    Returns:
        动作描述字符串
    """
    tab = '  '
    fields = []
    
    # 添加动作类型字段
    fields.append(f'- type: "{action.name}"')
    
    # 处理参数schema（简化版本）
    if action.param_schema:
        # 这里简化处理，只列出基本参数
        fields.append('- param:')
        if 'locate' in str(action.param_schema).lower():
            fields.append(f'  - locate: {locator_schema_type_description}')
    
    return f'''- {action.name}, {action.description or "No description provided"}
{tab}{chr(10).join(f"{tab}{f}" for f in fields)}'''.strip()


def system_prompt_to_task_planning(
    action_space: List[DeviceAction],
    include_bbox: bool = True
) -> str:
    """
    生成任务规划的系统提示词
    
    Args:
        action_space: 动作空间列表
        include_bbox: 是否包含bbox参数
    
    Returns:
        系统提示词
    """
    # 生成动作列表描述
    locator_schema_desc = get_vl_locate_param() if include_bbox else '{ prompt: string /* description of the target element */ }'
    
    action_descriptions = []
    for action in action_space:
        action_descriptions.append(description_for_action(action, locator_schema_desc))
    
    action_list = '\n'.join(action_descriptions)
    
    log_field_instruction = '''
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
'''

    common_output_fields = '''"error"?: string, // Error messages about unexpected situations, if any. Only think it is an error when the situation is not foreseeable according to the instruction. Use the same language as the user's instruction.
  "more_actions_needed_by_instruction": boolean, // Consider if there is still more action(s) to do after the action in "Log" is done, according to the instruction. If so, set this field to true. Otherwise, set it to false.'''

    # 生成示例
    bbox_example = ', "bbox": [100, 200, 300, 400]' if include_bbox else ''

    return f'''
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
        "prompt": "The login button"{bbox_example}
      }}
    }}
  }}
}}
'''

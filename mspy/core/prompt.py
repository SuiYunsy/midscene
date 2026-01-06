"""
提示词模块
Prompt module for AI
"""
from typing import Any, Dict, List, Optional


def bbox_description(vl_mode: Optional[str]) -> str:
    """
    Get bbox description based on VL mode.
    根据VL模式获取bbox描述
    """
    if vl_mode == "gemini":
        return "box_2d bounding box for the target element, should be [ymin, xmin, ymax, xmax] normalized to 0-1000."
    return "2d bounding box as [xmin, ymin, xmax, ymax]"


# Assertion schema
ASSERT_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "assert",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "pass": {
                    "type": "boolean",
                    "description": "Whether the assertion passed or failed",
                },
                "thought": {
                    "type": ["string", "null"],
                    "description": "The thought process behind the assertion",
                },
            },
            "required": ["pass", "thought"],
            "additionalProperties": False,
        },
    },
}


def vl_locate_param(vl_mode: Optional[str], include_bbox: bool = True) -> str:
    """
    Get VL locate parameter description.
    获取VL定位参数描述
    """
    if vl_mode and include_bbox:
        return f"{{bbox: [number, number, number, number], prompt: string }} // {bbox_description(vl_mode)}"
    return "{ prompt: string /* description of the target element */ }"


def description_for_action(
    action_name: str,
    action_description: str,
    param_fields: List[Dict[str, Any]],
    locator_schema_type_description: str,
) -> str:
    """
    Generate description for an action.
    生成动作描述
    """
    tab = "  "
    fields: List[str] = []
    
    # Add action type field
    fields.append(f'- type: "{action_name}"')
    
    if param_fields:
        param_lines: List[str] = []
        for field in param_fields:
            key = field.get("name", "")
            is_optional = field.get("optional", False)
            type_name = field.get("type", "any")
            description = field.get("description", "")
            
            # Check if it's a locator field
            if field.get("is_locator", False):
                type_name = locator_schema_type_description
            
            key_with_optional = f"{key}?" if is_optional else key
            param_line = f"{key_with_optional}: {type_name}"
            if description:
                param_line += f" // {description}"
            param_lines.append(param_line)
        
        if param_lines:
            fields.append("- param:")
            for line in param_lines:
                fields.append(f"  - {line}")
    
    return f"""- {action_name}, {action_description or 'No description provided'}
{tab}{chr(10).join(fields)}""".strip()


def get_log_field_instruction() -> str:
    """
    Get instruction for the log field.
    获取log字段的指令
    """
    return """
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


def system_prompt_to_task_planning(
    action_descriptions: List[str],
    vl_mode: Optional[str],
    include_bbox: bool = True,
) -> str:
    """
    Generate system prompt for task planning.
    生成任务规划的系统提示词
    
    Args:
        action_descriptions: List of action descriptions
        vl_mode: VL mode type
        include_bbox: Whether to include bbox in the response
        
    Returns:
        System prompt string
    """
    if include_bbox and not vl_mode:
        raise ValueError(
            "vl_mode cannot be undefined when include_bbox is true. "
            "A valid vl_mode is required for bbox-based location."
        )
    
    action_list = "\n".join(action_descriptions)
    log_field_instruction = get_log_field_instruction()
    
    common_output_fields = '''"error"?: string, // Error messages about unexpected situations, if any. Only think it is an error when the situation is not foreseeable according to the instruction. Use the same language as the user's instruction.
  "more_actions_needed_by_instruction": boolean, // Consider if there is still more action(s) to do after the action in "Log" is done, according to the instruction. If so, set this field to true. Otherwise, set it to false.'''
    
    bbox_example = f', "bbox": [100, 200, 300, 400]' if vl_mode and include_bbox else ''
    
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
        "prompt": "The login button"{bbox_example}
      }}
    }}
  }}
}}
"""

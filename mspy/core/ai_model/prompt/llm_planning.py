"""
LLM Planning Prompts

Corresponding to TypeScript source: packages/core/src/ai-model/prompt/llm-planning.ts
"""

from typing import Any, Dict, List, Optional
from mspy.core.ai_model.prompt.common import bbox_description


# Note: put the log field first to trigger the CoT

COMMON_OUTPUT_FIELDS = '''"error"?: string, // Error messages about unexpected situations, if any. Only think it is an error when the situation is not foreseeable according to the instruction. Use the same language as the user's instruction.
  "more_actions_needed_by_instruction": boolean, // Consider if there is still more action(s) to do after the action in "Log" is done, according to the instruction. If so, set this field to true. Otherwise, set it to false.'''


def vl_locate_param(vl_mode: Optional[str] = None) -> str:
    """Get the locate parameter format based on VL mode"""
    if vl_mode:
        return f'{{bbox: [number, number, number, number], prompt: string }} // {bbox_description(vl_mode)}'
    return '{ prompt: string /* description of the target element */ }'


def description_for_action(
    action: Dict[str, Any],
    locator_schema_type_description: str
) -> str:
    """Generate description for an action
    
    Args:
        action: Action dictionary with name, description, and optional param_schema
        locator_schema_type_description: Description for the locator schema type
        
    Returns:
        Action description string
    """
    tab = '  '
    fields = []
    
    # Add the action type field
    fields.append(f'- type: "{action.get("name", "Unknown")}"')
    
    # Handle param_schema if it exists
    if action.get('param_schema'):
        fields.append('- param:')
        # Simplified param handling - in real implementation would parse zod schema
        fields.append(f'  - locate: {locator_schema_type_description}')
    
    description = action.get('description', 'No description provided')
    return f'''- {action.get("name", "Unknown")}, {description}
{tab}{chr(10).join(fields)}'''.strip()


LOG_FIELD_INSTRUCTION = """
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
    action_space: List[Dict[str, Any]],
    vl_mode: Optional[str] = None,
    include_bbox: bool = False
) -> str:
    """Generate system prompt for task planning
    
    Args:
        action_space: List of available actions
        vl_mode: Vision-language mode type
        include_bbox: Whether to include bbox in locator
        
    Returns:
        System prompt for task planning
    """
    # Validate parameters
    if include_bbox and not vl_mode:
        raise ValueError(
            'vl_mode cannot be None when include_bbox is True. '
            'A valid vl_mode is required for bbox-based location.'
        )
    
    # Generate action descriptions
    action_descriptions = []
    for action in action_space:
        desc = description_for_action(
            action,
            vl_locate_param(vl_mode if include_bbox else None)
        )
        action_descriptions.append(desc)
    
    action_list = '\n'.join(action_descriptions)
    
    bbox_example = ', "bbox": [100, 200, 300, 400]' if (vl_mode and include_bbox) else ''
    
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

{LOG_FIELD_INSTRUCTION}

## Return format

Return in JSON format:
{{
  "log": string, // a brief preamble to the user explaining what you're about to do
  {COMMON_OUTPUT_FIELDS}
  "action": 
    {{
      "type": string, // the type of the action
      "param"?: {{ // The parameter of the action, if any
         // k-v style parameter fields
      }}
    }} | null,
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

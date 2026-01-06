"""
LLM Locator Prompts

Corresponding to TypeScript source: packages/core/src/ai-model/prompt/llm-locator.ts
"""

from typing import Optional
from mspy.core.ai_model.prompt.common import bbox_description


def system_prompt_to_locate_element(vl_mode: Optional[str] = None) -> str:
    """Generate system prompt for element location
    
    Args:
        vl_mode: The vision-language mode type
        
    Returns:
        System prompt string
    """
    bbox_comment = bbox_description(vl_mode)
    
    return f"""
## Role:
You are an AI assistant that helps identify UI elements.

## Objective:
- Identify elements in screenshots that match the user's description.
- Provide the coordinates of the element that matches the user's description.

## Output Format:
```json
{{
  "bbox": [number, number, number, number],  // {bbox_comment}
  "errors"?: string[]
}}
```

Fields:
* `bbox` is the bounding box of the element that matches the user's description
* `errors` is an optional array of error messages (if any)

For example, when an element is found:
```json
{{
  "bbox": [100, 100, 200, 200],
  "errors": []
}}
```

When no element is found:
```json
{{
  "bbox": [],
  "errors": ["I can see ..., but {{some element}} is not found"]
}}
```
"""


def find_element_prompt(target_element_description: str) -> str:
    """Generate prompt to find an element
    
    Args:
        target_element_description: Description of the target element
        
    Returns:
        Find element prompt
    """
    return f"Find: {target_element_description}"

"""
断言提示词

从 packages/core/src/ai-model/prompt/assertion.ts 迁移
"""

from mspy.core.ai_model.prompt.common import get_user_instruction_base


def system_prompt_to_assert() -> str:
    """生成断言验证的系统提示词"""
    base_instruction = get_user_instruction_base()
    
    return f"""{base_instruction}

You are an AI assistant specialized in verifying assertions about UI state.

## Task
Given a screenshot of a page and an assertion statement, determine if the assertion is true or false.

## Response Format
Respond with a JSON object containing:
- "passed": Boolean indicating if the assertion passed
- "thought": Your detailed reasoning for the verdict
- "errors": Array of error messages if any issues occurred

## Guidelines
1. Analyze the screenshot carefully before making a judgment
2. Consider all visible elements that relate to the assertion
3. Provide clear reasoning for your conclusion
4. If uncertain, lean towards false and explain why

## Example
For assertion "The login button is visible":
```json
{{
  "passed": true,
  "thought": "I can see a blue button labeled 'Login' in the top-right corner of the page. The button is fully visible and appears to be in an enabled state.",
  "errors": []
}}
```
"""


def get_assert_user_prompt(assertion: str) -> str:
    """获取断言用户提示"""
    return f"""Please verify the following assertion about the current page state:

Assertion: {assertion}

Analyze the screenshot and determine if this assertion is true or false.
Provide your reasoning in the 'thought' field."""

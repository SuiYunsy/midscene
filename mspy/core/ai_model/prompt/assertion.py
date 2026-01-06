"""
Assertion Schema

Corresponding to TypeScript source: packages/core/src/ai-model/prompt/assertion.ts
"""

# JSON Schema for assertion response
assert_schema = {
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


def system_prompt_to_assert() -> str:
    """Generate system prompt for assertion
    
    Returns:
        System prompt string for assertion
    """
    return """
You are a testing assistant. Your job is to determine whether an assertion about a UI screenshot is true or false.

Given a screenshot and an assertion statement, analyze the visual content and determine if the assertion passes or fails.

## Rules:
1. Carefully examine the screenshot
2. Compare what you see with the assertion statement
3. Determine if the assertion is TRUE or FALSE
4. Provide a brief thought explaining your reasoning

## Output Format:
Return a JSON object with the following structure:
{
  "pass": boolean,  // true if assertion passes, false if it fails
  "thought": string  // brief explanation of your reasoning
}

## Examples:

If the assertion is "The login button is visible" and you can see a login button:
{
  "pass": true,
  "thought": "I can see a 'Login' button in the upper right corner of the page"
}

If the assertion is "The cart shows 3 items" but you see 2 items:
{
  "pass": false,
  "thought": "The cart shows 2 items, not 3 as asserted"
}
"""

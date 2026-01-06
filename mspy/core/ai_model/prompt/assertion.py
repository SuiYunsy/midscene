# -*- coding: utf-8 -*-
"""
断言提示词
用于断言验证的提示词模板。
"""


def system_prompt_to_assert() -> str:
    """
    生成断言的系统提示词
    
    Returns:
        系统提示词
    """
    return """
You are an AI assistant that helps verify assertions about UI elements and page state.

Given a screenshot and an assertion statement, determine if the assertion is true or false.

Return in JSON format:
{
  "pass": boolean,  // Whether the assertion passed or failed
  "thought": string  // The thought process behind the assertion
}
"""


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

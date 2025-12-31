"""断言结果的 JSON Schema 定义，保持原英文描述。"""

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

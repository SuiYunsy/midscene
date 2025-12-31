"""LLM-based action planning."""

import json
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from midscene.shared.logger import get_logger
from midscene.core.types import UIContext, PlanningAction

logger = get_logger("ai:planning")


def _get_openai_client(model_config: Dict[str, Any]) -> AsyncOpenAI:
    """Get OpenAI client from model config."""
    return AsyncOpenAI(
        api_key=model_config.get("api_key"),
        base_url=model_config.get("base_url"),
    )


async def plan_action(
    context: UIContext,
    task_prompt: str,
    model_config: Dict[str, Any],
    ai_act_context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Plan actions to accomplish a task using AI.
    
    Args:
        context: UI context with screenshot
        task_prompt: Description of the task to accomplish
        model_config: Model configuration
        ai_act_context: Optional context about the page/app
        
    Returns:
        Dict with planned actions
    """
    client = _get_openai_client(model_config)
    model_name = model_config.get("model_name", "gpt-4o")
    
    action_space = """Available actions:
- Tap: Click on an element. Params: {"locate": {"prompt": "element description"}}
- DoubleClick: Double click. Params: {"locate": {"prompt": "element description"}}
- RightClick: Right click. Params: {"locate": {"prompt": "element description"}}
- Hover: Hover over element. Params: {"locate": {"prompt": "element description"}}
- Input: Type text. Params: {"locate": {"prompt": "element description"}, "value": "text to type"}
- KeyboardPress: Press key. Params: {"key_name": "Enter"}
- Scroll: Scroll page. Params: {"direction": "up|down|left|right", "distance": 300}
- Sleep: Wait. Params: {"time_ms": 1000}
- Finished: Task complete. Params: {}"""

    context_info = f"\nContext: {ai_act_context}" if ai_act_context else ""
    
    system_prompt = f"""You are a UI automation planner. Given a screenshot and a task,
plan the sequence of actions needed to accomplish the task.

{action_space}
{context_info}

Respond with a JSON object:
{{
    "thought": "Your reasoning about what to do",
    "actions": [
        {{"type": "ActionType", "param": {{...}}, "thought": "Why this action"}}
    ],
    "more_actions_needed": false
}}

Keep actions minimal and precise. Stop planning when the task is complete."""

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Task: {task_prompt}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{context.screenshot_base64}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Parse actions
        actions = []
        for action_data in result.get("actions", []):
            actions.append(PlanningAction(
                type=action_data.get("type", ""),
                param=action_data.get("param", {}),
                thought=action_data.get("thought"),
            ))
        
        return {
            "actions": actions,
            "thought": result.get("thought", ""),
            "more_actions_needed": result.get("more_actions_needed", False),
            "raw_response": content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
                "total_tokens": response.usage.total_tokens if response.usage else None,
            },
        }
        
    except Exception as e:
        logger.error("Error planning action: %s", str(e))
        return {"error": str(e), "actions": []}

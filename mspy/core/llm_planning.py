"""
LLM 规划模块
LLM Planning module
"""
from typing import Any, Dict, List, Optional

from ..shared import (
    get_debug,
    assert_condition,
    ModelConfig,
    UIContext,
    PlanningAction,
    PlanningAIResponse,
    padding_to_match_block_by_base64,
)

from .conversation_history import ConversationHistory
from .prompt import system_prompt_to_task_planning, vl_locate_param, description_for_action
from .service_caller import call_ai_with_object_response

debug = get_debug("planning")


def get_action_descriptions(
    action_space: List[Dict[str, Any]],
    vl_mode: Optional[str],
    include_bbox: bool,
) -> List[str]:
    """
    Generate action descriptions for prompt.
    生成用于提示词的动作描述
    """
    descriptions = []
    locator_type_desc = vl_locate_param(vl_mode, include_bbox)
    
    for action in action_space:
        name = action.get("name", "")
        desc = action.get("description", "No description provided")
        param_fields = action.get("param_fields", [])
        
        action_desc = description_for_action(
            name, desc, param_fields, locator_type_desc
        )
        descriptions.append(action_desc)
    
    return descriptions


def fill_bbox_param(
    locate: Dict[str, Any],
    width: int,
    height: int,
    right_limit: int,
    bottom_limit: int,
    vl_mode: Optional[str],
) -> Dict[str, Any]:
    """
    Fill and adapt bbox parameter in locate.
    填充和适配locate中的bbox参数
    """
    # Handle bbox_2d naming (Qwen hallucination)
    if "bbox_2d" in locate and "bbox" not in locate:
        locate["bbox"] = locate.pop("bbox_2d")
    
    if "bbox" not in locate:
        return locate
    
    bbox = locate["bbox"]
    if not isinstance(bbox, list) or len(bbox) < 4:
        return locate
    
    # Adapt bbox based on VL mode
    adapted_bbox = adapt_bbox(bbox, width, height, right_limit, bottom_limit, vl_mode)
    locate["bbox"] = adapted_bbox
    
    return locate


def adapt_bbox(
    bbox: List[Any],
    width: int,
    height: int,
    right_limit: int,
    bottom_limit: int,
    vl_mode: Optional[str],
) -> List[int]:
    """
    Adapt bbox coordinates based on VL mode.
    根据VL模式适配bbox坐标
    """
    # Normalize input
    if isinstance(bbox[0], list):
        bbox = bbox[0]
    
    # Convert to numbers
    bbox = [int(float(x)) if isinstance(x, (str, float)) else x for x in bbox]
    
    result = [0, 0, 0, 0]
    
    if vl_mode == "gemini":
        # Gemini: [ymin, xmin, ymax, xmax] normalized to 0-1000
        result = [
            round((bbox[1] * width) / 1000),
            round((bbox[0] * height) / 1000),
            round((bbox[3] * width) / 1000),
            round((bbox[2] * height) / 1000),
        ]
    elif vl_mode == "qwen3-vl":
        # Qwen3-VL: 0-1000 normalized
        result = [
            round((bbox[0] * width) / 1000),
            round((bbox[1] * height) / 1000),
            round((bbox[2] * width) / 1000),
            round((bbox[3] * height) / 1000),
        ]
    elif vl_mode in ("doubao-vision", "vlm-ui-tars"):
        # Doubao/UI-TARS: 0-1000 normalized
        result = [
            round((bbox[0] * width) / 1000),
            round((bbox[1] * height) / 1000),
            round((bbox[2] * width) / 1000),
            round((bbox[3] * height) / 1000),
        ]
    else:
        # Default: direct pixel values
        default_size = 20
        result = [
            round(bbox[0]),
            round(bbox[1]),
            round(bbox[2]) if len(bbox) > 2 else round(bbox[0] + default_size),
            round(bbox[3]) if len(bbox) > 3 else round(bbox[1] + default_size),
        ]
    
    # Clamp to limits
    result[2] = min(result[2], right_limit)
    result[3] = min(result[3], bottom_limit)
    
    return result


async def plan(
    user_instruction: str,
    context: UIContext,
    action_space: List[Dict[str, Any]],
    model_config: ModelConfig,
    conversation_history: ConversationHistory,
    include_bbox: bool = True,
    action_context: Optional[str] = None,
    images_include_count: Optional[int] = None,
) -> PlanningAIResponse:
    """
    Plan the next action based on user instruction.
    根据用户指令规划下一步动作
    
    Args:
        user_instruction: User's instruction
        context: UI context with screenshot
        action_space: Available actions
        model_config: Model configuration
        conversation_history: Conversation history
        include_bbox: Whether to include bbox in response
        action_context: Optional action context
        images_include_count: Number of images to include
        
    Returns:
        Planning AI response
    """
    screenshot_base64 = context.screenshot_base64
    size = context.size
    
    vl_mode = model_config.vl_mode
    
    # Generate system prompt
    action_descriptions = get_action_descriptions(action_space, vl_mode, include_bbox)
    system_prompt = system_prompt_to_task_planning(action_descriptions, vl_mode, include_bbox)
    
    # Prepare image payload
    image_payload = screenshot_base64
    image_width = size.width
    image_height = size.height
    right_limit = image_width
    bottom_limit = image_height
    
    # Pad image for qwen2.5-vl
    if vl_mode == "qwen2.5-vl":
        padded_result = padding_to_match_block_by_base64(image_payload)
        image_width = padded_result["width"]
        image_height = padded_result["height"]
        image_payload = padded_result["image_base64"]
    
    # Build instruction
    action_context_text = ""
    if action_context:
        action_context_text = f"<high_priority_knowledge>{action_context}</high_priority_knowledge>\n"
    
    instruction = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{action_context_text}<user_instruction>{user_instruction}</user_instruction>",
                }
            ],
        }
    ]
    
    # Build latest feedback message
    if conversation_history.pending_feedback_message:
        latest_feedback = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{conversation_history.pending_feedback_message}. The last screenshot is attached. Please going on according to the instruction.",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_payload, "detail": "high"},
                },
            ],
        }
        conversation_history.reset_pending_feedback_message_if_exists()
    else:
        latest_feedback = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "this is the latest screenshot",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_payload, "detail": "high"},
                },
            ],
        }
    
    conversation_history.append(latest_feedback)
    history_log = conversation_history.snapshot(images_include_count)
    
    # Build full message list
    messages = [
        {"role": "system", "content": system_prompt},
        *instruction,
        *history_log,
    ]
    
    # Call AI
    result = call_ai_with_object_response(messages, model_config)
    plan_from_ai = result["content"]
    raw_response = result["content_string"]
    usage = result.get("usage")
    
    # Parse actions
    actions = []
    if plan_from_ai.get("action"):
        action_data = plan_from_ai["action"]
        actions.append(
            PlanningAction(
                type=action_data.get("type", ""),
                param=action_data.get("param", {}),
                thought=plan_from_ai.get("log", ""),
            )
        )
    
    # Process bbox in locate params
    for action in actions:
        for key, value in action.param.items():
            if isinstance(value, dict) and ("prompt" in value or "bbox" in value):
                action.param[key] = fill_bbox_param(
                    value, image_width, image_height, right_limit, bottom_limit, vl_mode
                )
    
    response = PlanningAIResponse(
        actions=actions,
        more_actions_needed_by_instruction=plan_from_ai.get("more_actions_needed_by_instruction", False),
        log=plan_from_ai.get("log", ""),
        error=plan_from_ai.get("error"),
        sleep=plan_from_ai.get("sleep"),
        raw_response=raw_response,
    )
    
    assert_condition(plan_from_ai, "Can't get plans from AI")
    
    # Warn if no actions but more needed
    if (
        not actions
        and response.more_actions_needed_by_instruction
        and not response.sleep
    ):
        debug.warning(
            f"No actions planned but model said more actions needed: {user_instruction}"
        )
    
    # Append assistant response to history
    conversation_history.append({
        "role": "assistant",
        "content": [{"type": "text", "text": raw_response}],
    })
    
    return response

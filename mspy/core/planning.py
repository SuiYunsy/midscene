"""规划模块 - aiAct自动规划"""
from typing import Any, Dict, List, Optional
from .types import PlanningAction, PlanningResponse, UIContext
from .prompt import build_system_prompt
from .conversation import ConversationHistory
from .service import AIService
from ..shared.config import Config, get_config
from ..shared.logger import get_logger

logger = get_logger("planning")

# 默认动作空间定义
DEFAULT_ACTION_SPACE = [
    {
        "name": "Tap",
        "description": "Tap the element",
        "params": [
            {"name": "locate", "type": "object", "is_locate": True, "description": "The element to be tapped"},
        ],
    },
    {
        "name": "RightClick",
        "description": "Right click the element",
        "params": [
            {"name": "locate", "type": "object", "is_locate": True, "description": "The element to be right clicked"},
        ],
    },
    {
        "name": "DoubleClick",
        "description": "Double click the element",
        "params": [
            {"name": "locate", "type": "object", "is_locate": True, "description": "The element to be double clicked"},
        ],
    },
    {
        "name": "Hover",
        "description": "Move the mouse to the element",
        "params": [
            {"name": "locate", "type": "object", "is_locate": True, "description": "The element to be hovered"},
        ],
    },
    {
        "name": "Input",
        "description": "Input the value into the element",
        "params": [
            {"name": "value", "type": "string", "description": "The text to input"},
            {"name": "locate", "type": "object", "is_locate": True, "optional": True, 
             "description": "The position of the input field"},
            {"name": "mode", "type": "string", "optional": True, 
             "description": 'Input mode: "replace" (default), "append", or "clear"'},
        ],
    },
    {
        "name": "KeyboardPress",
        "description": 'Press a key or key combination, like "Enter", "Tab", "Control+A"',
        "params": [
            {"name": "keyName", "type": "string", "description": "The key to be pressed"},
            {"name": "locate", "type": "object", "is_locate": True, "optional": True,
             "description": "The element to click before pressing the key"},
        ],
    },
    {
        "name": "Scroll",
        "description": "Scroll the page or an element",
        "params": [
            {"name": "scrollType", "type": "string", "optional": True,
             "description": '"singleAction", "scrollToBottom", "scrollToTop", "scrollToRight", "scrollToLeft"'},
            {"name": "direction", "type": "string", "optional": True,
             "description": '"down", "up", "right", "left"'},
            {"name": "distance", "type": "number", "optional": True,
             "description": "The distance in pixels to scroll"},
            {"name": "locate", "type": "object", "is_locate": True, "optional": True,
             "description": "The target element to scroll on"},
        ],
    },
    {
        "name": "DragAndDrop",
        "description": "Drag and drop from one position to another",
        "params": [
            {"name": "from", "type": "object", "is_locate": True, "description": "The position to drag from"},
            {"name": "to", "type": "object", "is_locate": True, "description": "The position to drop to"},
        ],
    },
    {
        "name": "Navigate",
        "description": "Navigate the browser to a specified URL",
        "params": [
            {"name": "url", "type": "string", "description": "The URL to navigate to"},
        ],
    },
    {
        "name": "Reload",
        "description": "Reload the current page",
        "params": [],
    },
    {
        "name": "GoBack",
        "description": "Navigate back in browser history",
        "params": [],
    },
    {
        "name": "Print_Assert_Result",
        "description": "Print the result of the assertion",
        "params": [
            {"name": "condition", "type": "string", "description": "The condition of the assertion"},
            {"name": "thought", "type": "string", 
             "description": 'The thought of the assertion, like "I can see A, B, C on the page..."'},
            {"name": "result", "type": "boolean", "description": "The result of the assertion, true or false"},
        ],
    },
]

async def plan(
    user_instruction: str,
    context: UIContext,
    conversation_history: ConversationHistory,
    action_space: Optional[List[Dict[str, Any]]] = None,
    action_context: Optional[str] = None,
    max_images: Optional[int] = None,
    config: Optional[Config] = None,
) -> PlanningResponse:
    """
    执行一次规划，返回下一步动作
    """
    cfg = config or get_config()
    service = AIService(cfg)
    actions = action_space or DEFAULT_ACTION_SPACE
    # 构建系统提示词
    system_prompt = build_system_prompt(actions)
    # 构建用户指令消息
    action_ctx = f"<high_priority_knowledge>{action_context}</high_priority_knowledge>\n" if action_context else ""
    instruction_msg = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": f"{action_ctx}<user_instruction>{user_instruction}</user_instruction>",
            },
        ],
    }
    # 构建最新截图消息
    if conversation_history.pending_feedback_message:
        latest_msg = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{conversation_history.pending_feedback_message}. The last screenshot is attached. Please going on according to the instruction.",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": context.screenshot_base64, "detail": "high"},
                },
            ],
        }
        conversation_history.reset_pending_feedback()
    else:
        latest_msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": "this is the latest screenshot"},
                {
                    "type": "image_url",
                    "image_url": {"url": context.screenshot_base64, "detail": "high"},
                },
            ],
        }
    conversation_history.append(latest_msg)
    history_snapshot = conversation_history.snapshot(max_images)
    # 组装完整消息
    messages = [
        {"role": "system", "content": system_prompt},
        instruction_msg,
        *history_snapshot,
    ]
    # 调用AI
    try:
        parsed, raw_response, usage = await service.call_with_json_response(messages)
    except Exception as e:
        logger.error(f"AI调用失败: {e}")
        return PlanningResponse(
            log="",
            more_actions_needed=False,
            actions=[],
            error=str(e),
            raw_response="",
        )
    # 解析响应
    log_msg = parsed.get("log", "")
    more_needed = parsed.get("more_actions_needed_by_instruction", False)
    error = parsed.get("error")
    sleep_ms = parsed.get("sleep")
    action_data = parsed.get("action")
    actions_list = []
    if action_data:
        actions_list.append(PlanningAction(
            type=action_data.get("type", ""),
            param=action_data.get("param", {}),
            thought=log_msg,
        ))
    # 记录助手响应
    conversation_history.append({
        "role": "assistant",
        "content": [{"type": "text", "text": raw_response}],
    })
    return PlanningResponse(
        log=log_msg,
        more_actions_needed=more_needed,
        actions=actions_list,
        error=error,
        sleep=sleep_ms,
        raw_response=raw_response,
        usage=usage,
    )

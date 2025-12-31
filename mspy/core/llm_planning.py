"""
LLM规划模块
LLM planning for Midscene Python SDK
"""
from typing import List, Dict, Any, Optional

from ..shared import (
    get_debug,
    IModelConfig,
    PlanningAction,
    PlanningAIResponse,
    UIContext,
    assert_value,
)
from .conversation_history import ConversationHistory
from .prompt_planning import system_prompt_to_task_planning
from .service_caller import call_ai_with_object_response

debug = get_debug("planning")


class AIActionType:
    """AI动作类型常量"""
    PLAN = "plan"
    LOCATE = "locate"
    EXTRACT = "extract"
    ASSERT = "assert"
    DESCRIBE_ELEMENT = "describe_element"


def fill_bbox_param(
    locate_result: Dict[str, Any],
    image_width: int,
    image_height: int,
    right_limit: int,
    bottom_limit: int,
    vl_mode: str,
) -> Dict[str, Any]:
    """
    填充bbox参数
    
    Args:
        locate_result: 定位结果
        image_width: 图像宽度
        image_height: 图像高度
        right_limit: 右边界限制
        bottom_limit: 下边界限制
        vl_mode: VL模式
        
    Returns:
        处理后的定位结果
    """
    if not locate_result:
        return locate_result
    
    # 直接返回原始结果，bbox已经在AI响应中
    return locate_result


async def plan(
    user_instruction: str,
    context: UIContext,
    interface_type: str,
    action_space: List[Dict[str, Any]],
    model_config: IModelConfig,
    conversation_history: ConversationHistory,
    include_bbox: bool = True,
    action_context: Optional[str] = None,
    images_include_count: Optional[int] = None,
) -> PlanningAIResponse:
    """
    执行AI规划
    
    Args:
        user_instruction: 用户指令
        context: UI上下文
        interface_type: 接口类型
        action_space: 动作空间
        model_config: 模型配置
        conversation_history: 对话历史
        include_bbox: 是否包含bbox
        action_context: 动作上下文
        images_include_count: 图片包含数量
        
    Returns:
        PlanningAIResponse对象
    """
    screenshot_base64 = context.screenshot_base64
    size = context.size
    
    vl_mode = model_config.vl_mode
    
    # 生成系统提示词
    system_prompt = system_prompt_to_task_planning(
        action_space=action_space,
        include_bbox=include_bbox and vl_mode is not None,
    )
    
    image_payload = screenshot_base64
    image_width = size.width
    image_height = size.height
    right_limit = image_width
    bottom_limit = image_height
    
    # 构建action context
    action_context_str = ""
    if action_context:
        action_context_str = f"<high_priority_knowledge>{action_context}</high_priority_knowledge>\n"
    
    # 构建指令消息
    instruction = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{action_context_str}<user_instruction>{user_instruction}</user_instruction>",
                },
            ],
        }
    ]
    
    # 构建最新反馈消息
    if conversation_history.pending_feedback_message:
        latest_feedback_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{conversation_history.pending_feedback_message}. The last screenshot is attached. Please going on according to the instruction.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_payload,
                        "detail": "high",
                    },
                },
            ],
        }
        conversation_history.reset_pending_feedback_message_if_exists()
    else:
        latest_feedback_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "this is the latest screenshot",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_payload,
                        "detail": "high",
                    },
                },
            ],
        }
    
    conversation_history.append(latest_feedback_message)
    history_log = conversation_history.snapshot(images_include_count)
    
    # 构建消息列表
    msgs = [
        {"role": "system", "content": system_prompt},
        *instruction,
        *history_log,
    ]
    
    # 调用AI
    response = await call_ai_with_object_response(
        msgs,
        AIActionType.PLAN,
        model_config,
    )
    
    plan_from_ai = response.content
    raw_response = response.content_string
    usage = response.usage
    
    # 提取动作
    actions = []
    if plan_from_ai.get("action"):
        action_data = plan_from_ai["action"]
        actions.append(PlanningAction(
            type=action_data.get("type", ""),
            param=action_data.get("param", {}),
            thought=plan_from_ai.get("log", ""),
        ))
    
    # 构建返回值
    result = PlanningAIResponse(
        actions=actions,
        more_actions_needed_by_instruction=plan_from_ai.get("more_actions_needed_by_instruction", False),
        log=plan_from_ai.get("log", ""),
        sleep=plan_from_ai.get("sleep"),
        error=plan_from_ai.get("error"),
        usage=usage,
        raw_response=raw_response,
    )
    
    assert_value(plan_from_ai, "Cannot get plans from AI")
    
    # 处理动作中的定位字段
    for action in actions:
        action_type = action.type
        action_in_space = next(
            (a for a in action_space if a.get("name") == action_type),
            None
        )
        
        if action_in_space:
            param_schema = action_in_space.get("param_schema", {})
            for field_name, field_info in param_schema.items():
                if field_name == "locate" and action.param.get(field_name):
                    locate_result = action.param[field_name]
                    if vl_mode:
                        action.param[field_name] = fill_bbox_param(
                            locate_result,
                            image_width,
                            image_height,
                            right_limit,
                            bottom_limit,
                            vl_mode,
                        )
    
    # 检查是否没有动作但需要更多动作
    if not actions and result.more_actions_needed_by_instruction and not result.sleep:
        debug(f"No actions planned for the prompt, but model said more actions are needed: {user_instruction}")
    
    # 添加助手响应到历史
    conversation_history.append({
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": raw_response,
            },
        ],
    })
    
    return result

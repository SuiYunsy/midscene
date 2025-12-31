"""
LLM规划模块
"""

from typing import Any, Dict, List, Optional

from ...shared import (
    get_debug,
    IModelConfig,
    DeviceAction,
    PlanningAction,
    PlanningAIResponse,
    AIUsageInfo,
    UIContext,
)
from .conversation_history import ConversationHistory
from .prompt import system_prompt_to_task_planning
from .service_caller import call_ai_with_object_response

debug = get_debug('planning')

# 默认的bbox大小
DEFAULT_BBOX_SIZE = 20


def normalized_0_1000(
    bbox: List[int],
    width: int,
    height: int
) -> tuple:
    """
    将0-1000范围的bbox转换为实际像素坐标
    
    Args:
        bbox: [xmin, ymin, xmax, ymax] 0-1000范围
        width: 图像宽度
        height: 图像高度
    
    Returns:
        实际像素坐标
    """
    return (
        round(bbox[0] * width / 1000),
        round(bbox[1] * height / 1000),
        round(bbox[2] * width / 1000),
        round(bbox[3] * height / 1000),
    )


def adapt_bbox(
    bbox: Any,
    width: int,
    height: int,
    right_limit: int,
    bottom_limit: int,
    vl_mode: Optional[str] = None
) -> tuple:
    """
    适配bbox到实际坐标
    
    Args:
        bbox: 原始bbox数据
        width: 图像宽度
        height: 图像高度
        right_limit: 右边界限制
        bottom_limit: 下边界限制
        vl_mode: VL模式
    
    Returns:
        适配后的bbox (x1, y1, x2, y2)
    """
    # 处理嵌套数组
    if isinstance(bbox, list) and len(bbox) > 0 and isinstance(bbox[0], list):
        bbox = bbox[0]
    
    if not isinstance(bbox, (list, tuple)) or len(bbox) < 2:
        raise ValueError(f"Invalid bbox data: {bbox}")
    
    # 确保是数字列表
    bbox_nums = [int(x) if isinstance(x, (int, float)) else int(str(x).strip()) for x in bbox[:4]]
    
    # qwen3-vl 使用 0-1000 范围
    if vl_mode == 'qwen3-vl':
        result = normalized_0_1000(bbox_nums, width, height)
    else:
        # 默认处理
        result = tuple(bbox_nums)
    
    # 限制边界
    x1, y1, x2, y2 = result
    x2 = min(x2, right_limit)
    y2 = min(y2, bottom_limit)
    
    return (x1, y1, x2, y2)


def fill_bbox_param(
    locate: Dict[str, Any],
    width: int,
    height: int,
    right_limit: int,
    bottom_limit: int,
    vl_mode: Optional[str] = None
) -> Dict[str, Any]:
    """
    填充定位参数中的bbox
    
    Args:
        locate: 定位参数字典
        width: 图像宽度
        height: 图像高度
        right_limit: 右边界
        bottom_limit: 下边界
        vl_mode: VL模式
    
    Returns:
        处理后的定位参数
    """
    # 处理 bbox_2d 别名
    if locate.get('bbox_2d') and not locate.get('bbox'):
        locate['bbox'] = locate.pop('bbox_2d')
    
    if locate.get('bbox'):
        locate['bbox'] = adapt_bbox(
            locate['bbox'],
            width,
            height,
            right_limit,
            bottom_limit,
            vl_mode
        )
    
    return locate


def find_all_locate_fields(action: DeviceAction) -> List[str]:
    """
    查找动作定义中的所有定位字段
    
    Args:
        action: 设备动作
    
    Returns:
        定位字段名称列表
    """
    # 简化实现：检查常见的定位字段
    locate_fields = []
    
    # 检查常见的定位字段名
    common_locate_fields = ['locate', 'from', 'to', 'start', 'end']
    
    if action.param_schema:
        # 这里简化处理
        for field in common_locate_fields:
            if field in str(action.param_schema):
                locate_fields.append(field)
    
    return locate_fields


async def plan(
    user_instruction: str,
    context: UIContext,
    interface_type: str,
    action_space: List[DeviceAction],
    model_config: IModelConfig,
    conversation_history: ConversationHistory,
    include_bbox: bool = True,
    action_context: Optional[str] = None,
    images_include_count: Optional[int] = 2,
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
        images_include_count: 包含的图片数量
    
    Returns:
        规划AI响应
    """
    screenshot_base64 = context.screenshot_base64
    size = context.size
    
    image_width = size.width
    image_height = size.height
    right_limit = image_width
    bottom_limit = image_height
    
    # 生成系统提示词
    system_prompt = system_prompt_to_task_planning(
        action_space=action_space,
        include_bbox=include_bbox
    )
    
    # 构建用户指令
    action_context_str = ""
    if action_context:
        action_context_str = f"<high_priority_knowledge>{action_context}</high_priority_knowledge>\n"
    
    instruction = [{
        'role': 'user',
        'content': [{
            'type': 'text',
            'text': f"{action_context_str}<user_instruction>{user_instruction}</user_instruction>",
        }],
    }]
    
    # 构建反馈消息
    if conversation_history.pending_feedback_message:
        latest_feedback_message = {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': f"{conversation_history.pending_feedback_message}. The last screenshot is attached. Please going on according to the instruction.",
                },
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': screenshot_base64,
                        'detail': 'high',
                    },
                },
            ],
        }
        conversation_history.reset_pending_feedback_message_if_exists()
    else:
        latest_feedback_message = {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'this is the latest screenshot',
                },
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': screenshot_base64,
                        'detail': 'high',
                    },
                },
            ],
        }
    
    conversation_history.append(latest_feedback_message)
    history_log = conversation_history.snapshot(images_include_count)
    
    # 构建消息
    msgs = [
        {'role': 'system', 'content': system_prompt},
        *instruction,
        *history_log,
    ]
    
    # 调用AI
    response = await call_ai_with_object_response(msgs, model_config)
    
    plan_from_ai = response['content']
    raw_response = response['content_string']
    usage = response.get('usage')
    
    # 解析响应
    actions = []
    if plan_from_ai.get('action'):
        action_data = plan_from_ai['action']
        action = PlanningAction(
            type=action_data.get('type', ''),
            param=action_data.get('param', {}),
            thought=plan_from_ai.get('log', ''),
        )
        actions.append(action)
    
    # 处理定位参数中的bbox
    for action in actions:
        action_type = action.type
        action_in_space = None
        for a in action_space:
            if a.name == action_type:
                action_in_space = a
                break
        
        if action_in_space:
            locate_fields = find_all_locate_fields(action_in_space)
            for field in locate_fields:
                locate_result = action.param.get(field)
                if locate_result and model_config.vl_mode:
                    action.param[field] = fill_bbox_param(
                        locate_result,
                        image_width,
                        image_height,
                        right_limit,
                        bottom_limit,
                        model_config.vl_mode
                    )
    
    result = PlanningAIResponse(
        actions=actions,
        more_actions_needed_by_instruction=plan_from_ai.get('more_actions_needed_by_instruction', False),
        log=plan_from_ai.get('log', ''),
        sleep=plan_from_ai.get('sleep'),
        error=plan_from_ai.get('error'),
        usage=usage,
        raw_response=raw_response,
    )
    
    if not actions and result.more_actions_needed_by_instruction and not result.sleep:
        debug(f"No actions planned for the prompt, but model said more actions are needed: {user_instruction}")
    
    # 将响应添加到对话历史
    conversation_history.append({
        'role': 'assistant',
        'content': [{
            'type': 'text',
            'text': raw_response,
        }],
    })
    
    return result

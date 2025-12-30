"""
AI Model - AI 模型调用模块
使用 OpenAI SDK 调用 LLM
"""

import json
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from mspy.shared.types import AIUsageInfo, IModelConfig, PlanningAction, PlanningAIResponse
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition, safe_parse_json, extract_json_from_code_block
from mspy.core.types import ConversationHistory
from mspy.core.prompts import system_prompt_to_task_planning


debug_call = get_debug("ai:call")
debug_profile_stats = get_debug("ai:profile:stats")


def create_chat_client(
    model_config: IModelConfig,
) -> Tuple[OpenAI, str, str, Optional[str]]:
    """
    创建 OpenAI 聊天客户端
    
    Args:
        model_config: 模型配置
        
    Returns:
        (client, model_name, model_description, vl_mode)
    """
    debug_proxy = get_debug("ai:call:proxy")
    
    # 处理代理
    http_client = None
    if model_config.http_proxy:
        debug_proxy("using http proxy", model_config.http_proxy.split("@")[-1])
        try:
            import httpx
            http_client = httpx.Client(proxy=model_config.http_proxy)
        except ImportError:
            debug_proxy("httpx not installed, proxy will not be used")
    
    # 创建 OpenAI 客户端
    client_kwargs = {
        "api_key": model_config.openai_api_key,
        "base_url": model_config.openai_base_url,
    }
    
    if model_config.timeout:
        client_kwargs["timeout"] = model_config.timeout
    
    if http_client:
        client_kwargs["http_client"] = http_client
    
    if model_config.openai_extra_config:
        client_kwargs.update(model_config.openai_extra_config)
    
    client = OpenAI(**client_kwargs)
    
    # 如果提供了自定义客户端工厂（同步调用）
    if model_config.create_openai_client:
        wrapped_client = model_config.create_openai_client(client, client_kwargs)
        if wrapped_client:
            client = wrapped_client
    
    return (
        client,
        model_config.model_name,
        model_config.model_description,
        model_config.vl_mode,
    )


def build_usage_info(
    usage_data: Optional[Dict[str, Any]],
    time_cost: Optional[float],
    model_name: str,
    model_description: str,
    intent: str,
) -> Optional[AIUsageInfo]:
    """
    构建使用信息
    
    Args:
        usage_data: OpenAI 返回的使用数据
        time_cost: 耗时
        model_name: 模型名称
        model_description: 模型描述
        intent: 意图
        
    Returns:
        AIUsageInfo 对象
    """
    if not usage_data:
        return None
    
    # 验证 usage_data 是字典类型
    if not isinstance(usage_data, dict):
        return None
    
    cached_input = None
    prompt_details = usage_data.get("prompt_tokens_details", {})
    if isinstance(prompt_details, dict):
        cached_input = prompt_details.get("cached_tokens")
    
    return AIUsageInfo(
        prompt_tokens=usage_data.get("prompt_tokens"),
        completion_tokens=usage_data.get("completion_tokens"),
        total_tokens=usage_data.get("total_tokens"),
        cached_input=cached_input,
        time_cost=time_cost,
        model_name=model_name,
        model_description=model_description,
        intent=intent,
    )


def call_ai(
    messages: List[Dict[str, Any]],
    model_config: IModelConfig,
) -> Dict[str, Any]:
    """
    调用 AI 模型
    
    Args:
        messages: 消息列表
        model_config: 模型配置
        
    Returns:
        包含 content, usage, is_streamed 的字典
    """
    debug_call("sending request to", model_config.model_name)
    
    # 创建客户端
    client_kwargs = {
        "api_key": model_config.openai_api_key,
        "base_url": model_config.openai_base_url,
    }
    
    if model_config.timeout:
        client_kwargs["timeout"] = model_config.timeout
    
    if model_config.openai_extra_config:
        client_kwargs.update(model_config.openai_extra_config)
    
    client = OpenAI(**client_kwargs)
    
    start_time = time.time()
    temperature = model_config.temperature if model_config.temperature is not None else 0
    
    try:
        # 构建请求参数
        request_params = {
            "model": model_config.model_name,
            "messages": messages,
            "temperature": temperature,
        }
        
        # qwen-vl 特殊配置
        if model_config.vl_mode == "qwen2.5-vl":
            request_params["vl_high_resolution_images"] = True
        
        result = client.chat.completions.create(**request_params)
        
        time_cost = time.time() - start_time
        
        debug_profile_stats(
            f"model={model_config.model_name}, "
            f"mode={model_config.vl_mode or 'default'}, "
            f"prompt_tokens={result.usage.prompt_tokens if result.usage else 'N/A'}, "
            f"completion_tokens={result.usage.completion_tokens if result.usage else 'N/A'}, "
            f"cost_ms={int(time_cost * 1000)}"
        )
        
        assert_condition(result.choices, f"Invalid response from LLM: {result}")
        
        content = result.choices[0].message.content
        assert_condition(content, "Empty content from LLM")
        
        usage_dict = None
        if result.usage:
            usage_dict = {
                "prompt_tokens": result.usage.prompt_tokens,
                "completion_tokens": result.usage.completion_tokens,
                "total_tokens": result.usage.total_tokens,
            }
        
        usage_info = build_usage_info(
            usage_dict,
            time_cost,
            model_config.model_name,
            model_config.model_description,
            model_config.intent,
        )
        
        debug_call("response:", content[:200] if len(content) > 200 else content)
        
        return {
            "content": content,
            "usage": usage_info,
            "is_streamed": False,
        }
        
    except Exception as e:
        error_msg = f"Failed to call AI model ({model_config.model_name}): {str(e)}"
        debug_call("error:", error_msg)
        raise RuntimeError(error_msg) from e


def call_ai_with_object_response(
    messages: List[Dict[str, Any]],
    model_config: IModelConfig,
) -> Dict[str, Any]:
    """
    调用 AI 并解析 JSON 响应
    
    Args:
        messages: 消息列表
        model_config: 模型配置
        
    Returns:
        包含 content (解析后的对象), content_string, usage 的字典
    """
    response = call_ai(messages, model_config)
    assert_condition(response, "Empty response from AI")
    
    content_str = response["content"]
    json_content = safe_parse_json(content_str)
    
    assert_condition(
        isinstance(json_content, dict),
        f"Failed to parse JSON response from model ({model_config.model_name}): {content_str}"
    )
    
    return {
        "content": json_content,
        "content_string": content_str,
        "usage": response.get("usage"),
    }


def fill_bbox_param(
    locate: Dict[str, Any],
    width: int,
    height: int,
    right_limit: int,
    bottom_limit: int,
    vl_mode: Optional[str],
) -> Dict[str, Any]:
    """
    填充 bbox 参数
    
    Args:
        locate: 定位参数
        width: 图像宽度
        height: 图像高度
        right_limit: 右边界
        bottom_limit: 下边界
        vl_mode: VL 模式
        
    Returns:
        处理后的定位参数
    """
    # Qwen 模型可能将 bbox 命名为 bbox_2d
    if "bbox_2d" in locate and "bbox" not in locate:
        locate["bbox"] = locate.pop("bbox_2d")
    
    if "bbox" in locate and locate["bbox"]:
        locate["bbox"] = adapt_bbox(
            locate["bbox"],
            width,
            height,
            right_limit,
            bottom_limit,
            vl_mode,
        )
    
    return locate


def adapt_bbox(
    bbox: Union[List[int], List[float]],
    width: int,
    height: int,
    right_limit: int,
    bottom_limit: int,
    vl_mode: Optional[str],
) -> List[int]:
    """
    适配 bbox 坐标
    
    Args:
        bbox: 原始 bbox
        width: 图像宽度
        height: 图像高度
        right_limit: 右边界
        bottom_limit: 下边界
        vl_mode: VL 模式
        
    Returns:
        适配后的 bbox [x1, y1, x2, y2]
    """
    # 处理嵌套数组
    if bbox and isinstance(bbox[0], list):
        bbox = bbox[0]
    
    result = [0, 0, 0, 0]
    
    if vl_mode in ("qwen2.5-vl", "qwen3-vl"):
        # 0-1000 归一化坐标
        result = [
            round(bbox[0] * width / 1000),
            round(bbox[1] * height / 1000),
            round(bbox[2] * width / 1000),
            round(bbox[3] * height / 1000),
        ]
    else:
        # 直接使用像素坐标
        default_bbox_size = 20
        result = [
            round(bbox[0]),
            round(bbox[1]),
            round(bbox[2]) if len(bbox) > 2 else round(bbox[0] + default_bbox_size),
            round(bbox[3]) if len(bbox) > 3 else round(bbox[1] + default_bbox_size),
        ]
    
    # 限制边界
    result[2] = min(result[2], right_limit)
    result[3] = min(result[3], bottom_limit)
    
    return result


def plan(
    user_instruction: str,
    context_screenshot_base64: str,
    context_size: Dict[str, int],
    interface_type: str,
    action_space: List[Any],
    model_config: IModelConfig,
    conversation_history: ConversationHistory,
    include_bbox: bool = False,
    action_context: Optional[str] = None,
    images_include_count: Optional[int] = None,
) -> PlanningAIResponse:
    """
    执行规划
    
    Args:
        user_instruction: 用户指令
        context_screenshot_base64: 截图 base64
        context_size: 上下文尺寸 {width, height}
        interface_type: 接口类型
        action_space: 动作空间
        model_config: 模型配置
        conversation_history: 对话历史
        include_bbox: 是否包含 bbox
        action_context: 动作上下文
        images_include_count: 包含的图片数量
        
    Returns:
        规划 AI 响应
    """
    debug = get_debug("planning")
    
    vl_mode = model_config.vl_mode
    
    # 生成系统提示词
    system_prompt = system_prompt_to_task_planning(
        action_space=action_space,
        vl_mode=vl_mode,
        include_bbox=include_bbox,
    )
    
    image_payload = context_screenshot_base64
    image_width = context_size["width"]
    image_height = context_size["height"]
    right_limit = image_width
    bottom_limit = image_height
    
    # 构建动作上下文
    action_context_text = ""
    if action_context:
        action_context_text = f"<high_priority_knowledge>{action_context}</high_priority_knowledge>\n"
    
    # 构建指令消息
    instruction = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{action_context_text}<user_instruction>{user_instruction}</user_instruction>",
                },
            ],
        },
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
    
    # 构建完整消息
    messages = [
        {"role": "system", "content": system_prompt},
        *instruction,
        *history_log,
    ]
    
    # 调用 AI
    response = call_ai_with_object_response(messages, model_config)
    
    plan_from_ai = response["content"]
    raw_response = response["content_string"]
    usage = response.get("usage")
    
    # 处理动作
    actions = []
    if plan_from_ai.get("action"):
        actions = [plan_from_ai["action"]]
    
    # 填充 bbox 参数
    for action in actions:
        action_type = action.get("type")
        param = action.get("param", {})
        
        # 查找动作空间中的定义
        action_def = next(
            (a for a in action_space if a.name == action_type),
            None
        )
        
        if action_def and param:
            # 处理 locate 字段
            locate_fields = ["locate", "from", "to", "start", "end"]
            for field in locate_fields:
                if field in param and param[field] and vl_mode:
                    param[field] = fill_bbox_param(
                        param[field],
                        image_width,
                        image_height,
                        right_limit,
                        bottom_limit,
                        vl_mode,
                    )
    
    # 构建响应
    response_obj = PlanningAIResponse(
        actions=[
            PlanningAction(
                type=a.get("type", ""),
                param=a.get("param", {}),
                thought=a.get("thought"),
            )
            for a in actions
        ],
        more_actions_needed_by_instruction=plan_from_ai.get("more_actions_needed_by_instruction", False),
        log=plan_from_ai.get("log", ""),
        sleep=plan_from_ai.get("sleep"),
        error=plan_from_ai.get("error"),
        usage=usage,
        raw_response=raw_response,
    )
    
    # 检查警告
    if (
        not actions
        and response_obj.more_actions_needed_by_instruction
        and not response_obj.sleep
    ):
        debug(
            f"No actions planned for the prompt, but model said more actions are needed: {user_instruction}"
        )
    
    # 添加助手消息到对话历史
    conversation_history.append({
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": raw_response,
            },
        ],
    })
    
    return response_obj

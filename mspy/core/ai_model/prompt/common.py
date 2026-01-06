"""
通用提示词

从 packages/core/src/ai-model/prompt/common.ts 迁移
"""

from mspy.shared.env import get_preferred_language


# 系统角色提示
SYSTEM_ROLE_PROMPT = """You are a versatile professional in software UI automation. You can analyze the UI and perform the planning based on the user's intent and the context of the page."""


def get_user_instruction_base() -> str:
    """获取用户指令基础"""
    language = get_preferred_language()
    return f"Please respond in {language}."


def get_element_description_prompt() -> str:
    """获取元素描述提示"""
    return """Describe the UI element marked with the red box in the image. 
The description should be:
1. Concise and clear
2. Focus on the element's visual characteristics and purpose
3. Suitable for use as a locator prompt to find this element again"""


def get_planning_context_prompt(context: str) -> str:
    """获取规划上下文提示"""
    return f"""
## Context Information
The user has provided the following context for this task:
{context}

Please consider this context when planning and executing actions.
"""

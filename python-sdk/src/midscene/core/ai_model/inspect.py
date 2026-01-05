"""Element inspection and data extraction using AI."""

import json
from typing import Any, Dict, List, Optional, Tuple, Union

from openai import AsyncOpenAI

from midscene.shared.logger import get_logger
from midscene.core.types import UIContext, Rect

logger = get_logger("ai:inspect")


def _get_openai_client(model_config: Dict[str, Any]) -> AsyncOpenAI:
    """Get OpenAI client from model config."""
    return AsyncOpenAI(
        api_key=model_config.get("api_key"),
        base_url=model_config.get("base_url"),
    )


async def locate_element(
    context: UIContext,
    target_description: str,
    model_config: Dict[str, Any],
    deep_think: bool = False,
) -> Dict[str, Any]:
    """
    Locate an element on the page using AI.
    
    Args:
        context: UI context with screenshot
        target_description: Description of element to find
        model_config: Model configuration
        deep_think: Whether to use deep thinking
        
    Returns:
        Dict with element info or error
    """
    client = _get_openai_client(model_config)
    model_name = model_config.get("model_name", "gpt-4o")
    
    system_prompt = """You are a UI element locator. Given a screenshot and a description,
find the element that best matches the description and return its bounding box.

Respond with a JSON object:
{
    "bbox": [x, y, width, height],  // bounding box in pixels
    "description": "description of the found element",
    "confidence": 0.95  // confidence score 0-1
}

If the element cannot be found, respond with:
{
    "error": "reason why element was not found"
}"""

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Find this element: {target_description}"},
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
        
        if "error" in result:
            return {"error": result["error"]}
        
        bbox = result.get("bbox", [0, 0, 0, 0])
        
        return {
            "element": {
                "description": result.get("description", target_description),
                "center": (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2),
                "rect": Rect(
                    left=bbox[0],
                    top=bbox[1],
                    width=bbox[2],
                    height=bbox[3],
                ),
            },
            "raw_response": content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
                "total_tokens": response.usage.total_tokens if response.usage else None,
            },
        }
        
    except Exception as e:
        logger.error("Error locating element: %s", str(e))
        return {"error": str(e)}


async def extract_data(
    context: UIContext,
    data_query: Union[str, Dict[str, str]],
    model_config: Dict[str, Any],
    options: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Extract data from the page using AI.
    
    Args:
        context: UI context with screenshot
        data_query: Query describing what data to extract
        model_config: Model configuration
        options: Extraction options
        
    Returns:
        Dict with extracted data
    """
    client = _get_openai_client(model_config)
    model_name = model_config.get("model_name", "gpt-4o")
    
    if isinstance(data_query, dict):
        query_str = json.dumps(data_query)
        system_prompt = f"""You are a data extractor. Extract the requested data from the screenshot.
        
Return a JSON object with the same keys as the query, filled with the extracted values:
{query_str}"""
    else:
        system_prompt = f"""You are a data extractor. Extract the requested data from the screenshot.
        
Query: {data_query}

Return a JSON object with the extracted data."""

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract the data from this screenshot:"},
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
        data = json.loads(content)
        
        return {
            "data": data,
            "raw_response": content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
                "total_tokens": response.usage.total_tokens if response.usage else None,
            },
        }
        
    except Exception as e:
        logger.error("Error extracting data: %s", str(e))
        return {"error": str(e)}


async def describe_element(
    context: UIContext,
    target: Union[Tuple[float, float], Rect],
    model_config: Dict[str, Any],
    deep_think: bool = False,
) -> Dict[str, Any]:
    """
    Describe an element at a position.
    
    Args:
        context: UI context with screenshot
        target: Target position or rect
        model_config: Model configuration
        deep_think: Whether to use deep thinking
        
    Returns:
        Dict with element description
    """
    client = _get_openai_client(model_config)
    model_name = model_config.get("model_name", "gpt-4o")
    
    # Convert target to description
    if isinstance(target, tuple):
        target_desc = f"the element at coordinates ({target[0]}, {target[1]})"
    else:
        target_desc = f"the element in the box at ({target.left}, {target.top}) with size ({target.width}x{target.height})"
    
    system_prompt = """You are a UI element describer. Given a screenshot and a target location,
describe the element at that location in a way that would allow someone to find it again.

Return a JSON object:
{
    "description": "A concise, unique description of the element"
}"""

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Describe {target_desc}:"},
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
        
        return {
            "description": result.get("description", ""),
            "raw_response": content,
        }
        
    except Exception as e:
        logger.error("Error describing element: %s", str(e))
        return {"error": str(e)}

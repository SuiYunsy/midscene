"""
Common utilities for prompts

Corresponding to TypeScript source: packages/core/src/ai-model/prompt/common.ts
"""

from typing import Optional


def bbox_description(vl_mode: Optional[str] = None) -> str:
    """Get the bbox description based on VL mode
    
    Args:
        vl_mode: The vision-language mode type
        
    Returns:
        Description string for bbox format
    """
    if vl_mode == 'gemini':
        return 'box_2d bounding box for the target element, should be [ymin, xmin, ymax, xmax] normalized to 0-1000.'
    return '2d bounding box as [xmin, ymin, xmax, ymax]'

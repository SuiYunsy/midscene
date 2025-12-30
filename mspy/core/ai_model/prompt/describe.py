# -*- coding: utf-8 -*-
"""
元素描述提示词
用于描述页面元素的提示词模板。
"""

from mspy.shared.env import get_preferred_language


def element_describer_instruction() -> str:
    """
    获取元素描述指令
    
    Returns:
        元素描述提示词
    """
    return f"""
Describe the element in the red rectangle for precise identification. Use {get_preferred_language()}.

CRITICAL REQUIREMENTS:
1. UNIQUENESS: The description must uniquely identify this element on the current page
2. UNIVERSALITY: Use generic, reusable selectors that work across different contexts
3. PRECISION: Be specific enough to distinguish from similar elements

DESCRIPTION STRUCTURE:
1. Element type (button, input, link, div, etc.)
2. Primary identifier (in order of preference):
   - Unique text content: "with text 'Login'"
   - Unique attribute: "with aria-label 'Search'"
   - Unique class/ID: "with class 'primary-button'"
   - Unique position: "in header navigation"
3. Secondary identifiers (if needed for uniqueness):
   - Visual features: "blue background", "with icon"
   - Relative position: "below search bar", "in sidebar"
   - Parent context: "in login form", "in main menu"

GUIDELINES:
- Keep description under 25 words
- Prioritize semantic identifiers over visual ones
- Use consistent terminology across similar elements
- Avoid page-specific or temporary content
- Don't mention the red rectangle or selection box
- Focus on stable, reusable characteristics

EXAMPLES:
- "Login button with text 'Sign In'"
- "Search input with placeholder 'Enter keywords'"
- "Navigation link with text 'Home' in header"
- "Submit button in contact form"
- "Menu icon with aria-label 'Open menu'"

Return JSON:
{{
  "description": "unique element identifier",
  "error"?: "error message if any"
}}"""

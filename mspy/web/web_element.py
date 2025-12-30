"""
Web元素处理

对应TypeScript源码: packages/web-integration/src/web-element.ts
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from mspy.shared.types import Rect, NodeType
from mspy.core.types import UIContext


@dataclass
class WebElementInfo:
    """Web元素信息
    
    表示页面上的一个元素
    """
    content: str
    rect: Rect
    center: tuple  # [x, y]
    id: str
    index_id: int
    attributes: Dict[str, str]
    xpaths: Optional[List[str]] = None
    is_visible: bool = True


class WebElementInfoImpl(WebElementInfo):
    """Web元素信息实现类"""
    
    def __init__(
        self,
        content: str,
        rect: Rect,
        id: str,
        attributes: Dict[str, str],
        index_id: int,
        xpaths: Optional[List[str]] = None,
        is_visible: bool = True,
    ):
        # 计算中心点
        center = (
            int(rect.left + rect.width / 2),
            int(rect.top + rect.height / 2)
        )
        
        super().__init__(
            content=content,
            rect=rect,
            center=center,
            id=id,
            index_id=index_id,
            attributes=attributes,
            xpaths=xpaths,
            is_visible=is_visible,
        )


async def WebPageContextParser(page: Any, opts: Optional[Dict[str, Any]] = None) -> UIContext:
    """解析Web页面上下文
    
    Args:
        page: 页面对象（需要实现AbstractInterface）
        opts: 选项
        
    Returns:
        UI上下文
    """
    # 使用页面的getContext方法
    if hasattr(page, 'get_context'):
        return await page.get_context()
    
    # 手动构建上下文
    from mspy.web.playwright.page import SimpleUIContext
    
    screenshot = await page.screenshot_base64()
    size = await page.size()
    
    return SimpleUIContext(screenshot, size)


# 限制新标签页脚本
LIMIT_OPEN_NEW_TAB_SCRIPT = '''
if (!window.__MIDSCENE_NEW_TAB_INTERCEPTOR_INITIALIZED__) {
  window.__MIDSCENE_NEW_TAB_INTERCEPTOR_INITIALIZED__ = true;

  // 拦截 window.open 方法
  window.open = function(url) {
    console.log('Blocked window.open:', url);
    window.location.href = url;
    return null;
  };

  // 阻止所有 target="_blank" 的链接
  document.addEventListener('click', function(e) {
    const target = e.target.closest('a');
    if (target && target.target === '_blank') {
      e.preventDefault();
      console.log('Blocked new tab:', target.href);
      window.location.href = target.href;
      target.removeAttribute('target');
    }
  }, true);
}
'''

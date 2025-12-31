"""
YAML脚本播放器创建

提供创建YAML播放器的便捷函数。
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from playwright.async_api import async_playwright, Browser

from mspy.core.yaml import ScriptPlayer, parse_yaml_script
from mspy.core.yaml.player import FreeFn
from mspy.core.yaml.parser import MidsceneYamlScript
from mspy.core.agent import Agent, AgentOpt
from mspy.web.playwright import PlaywrightPage
from mspy.shared.logger import get_debug

logger = logging.getLogger("midscene.cli")
debug = get_debug("create-yaml-player")


async def create_yaml_player(
    file: str,
    script: Optional[MidsceneYamlScript] = None,
    options: Optional[Dict[str, Any]] = None,
) -> ScriptPlayer:
    """
    创建YAML脚本播放器
    
    Args:
        file: YAML文件路径
        script: 预解析的脚本（可选）
        options: 选项配置
            - headed: 是否有头模式
            - keep_window: 是否保持窗口
            - browser: 共享的浏览器实例
            - test_id: 测试ID
            
    Returns:
        ScriptPlayer实例
    """
    options = options or {}
    
    # 解析脚本
    if script is None:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        yaml_script = parse_yaml_script(content, file)
    else:
        yaml_script = script
    
    file_name = Path(file).stem
    
    async def setup_agent(platform: Any) -> tuple[Agent, List[FreeFn]]:
        """设置Agent"""
        free_fn: List[FreeFn] = []
        web_target = yaml_script.web or yaml_script.target
        
        if web_target:
            # 使用Playwright
            headed = options.get("headed", False)
            keep_window = options.get("keep_window", False)
            shared_browser = options.get("browser")
            
            pw = None
            browser = shared_browser
            
            if browser is None:
                pw = await async_playwright().start()
                browser = await pw.chromium.launch(headless=not headed)
                
                async def close_browser() -> None:
                    try:
                        await browser.close()
                    except Exception:
                        pass
                    if pw:
                        try:
                            await pw.stop()
                        except Exception:
                            pass
                
                free_fn.append(FreeFn("close_browser", close_browser))
            
            # 创建上下文和页面
            viewport_width = getattr(web_target, "viewport_width", None) or 1280
            viewport_height = getattr(web_target, "viewport_height", None) or 720
            
            context_opts: Dict[str, Any] = {
                "viewport": {"width": viewport_width, "height": viewport_height},
            }
            
            user_agent = getattr(web_target, "user_agent", None)
            if user_agent:
                context_opts["user_agent"] = user_agent
            
            context = await browser.new_context(**context_opts)
            page = await context.new_page()
            
            async def close_context() -> None:
                if not keep_window:
                    try:
                        await context.close()
                    except Exception:
                        pass
            
            free_fn.append(FreeFn("close_context", close_context))
            
            # 导航到URL
            url = getattr(web_target, "url", None)
            if url:
                debug(f"Navigating to {url}")
                await page.goto(url)
                
                # 等待网络空闲
                wait_for_network_idle = getattr(web_target, "wait_for_network_idle", True)
                if wait_for_network_idle:
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        debug("Network idle timeout, continuing anyway")
            
            # 创建页面封装
            playwright_page = PlaywrightPage(page)
            
            # 创建Agent
            test_id = options.get("test_id") or getattr(yaml_script.agent, "test_id", None) or file_name
            
            agent_opts = AgentOpt(
                test_id=test_id,
            )
            
            agent = Agent(playwright_page, agent_opts)
            
            async def destroy_agent() -> None:
                try:
                    await agent.destroy()
                except Exception:
                    pass
            
            free_fn.append(FreeFn("destroy_agent", destroy_agent))
            
            return agent, free_fn
        
        raise ValueError(
            "No valid interface configuration found in the YAML script. "
            "Should have 'web' configuration."
        )
    
    player = ScriptPlayer(
        script=yaml_script,
        setup_agent=setup_agent,
        script_path=file,
    )
    
    return player

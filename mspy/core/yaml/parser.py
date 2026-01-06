"""
YAML脚本解析器

对应TypeScript源码: packages/core/src/yaml/index.ts
"""

import yaml
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class MidsceneYamlFlowItem:
    """YAML流程项
    
    表示脚本中的单个操作步骤
    """
    # 动作类型
    ai_act: Optional[str] = None  # 对应 aiAct
    ai_tap: Optional[str] = None  # 对应 aiTap
    ai_hover: Optional[str] = None  # 对应 aiHover
    ai_input: Optional[Dict[str, str]] = None  # 对应 aiInput
    ai_keyboard_press: Optional[str] = None  # 对应 aiKeyboardPress
    ai_scroll: Optional[Dict[str, Any]] = None  # 对应 aiScroll
    ai_assert: Optional[str] = None  # 对应 aiAssert
    ai_wait_for: Optional[str] = None  # 对应 aiWaitFor
    ai_query: Optional[Union[str, Dict[str, str]]] = None  # 对应 aiQuery
    
    # 控制流
    sleep: Optional[int] = None  # 休眠毫秒数
    log: Optional[str] = None  # 日志输出
    
    # 条件和循环（扩展）
    condition: Optional[str] = None
    loop: Optional[int] = None


@dataclass
class MidsceneYamlTask:
    """YAML任务
    
    表示一组相关的操作流程
    """
    name: str
    flow: List[MidsceneYamlFlowItem] = field(default_factory=list)
    continue_on_error: bool = False


@dataclass
class MidsceneYamlScriptWebEnv:
    """Web环境配置"""
    url: Optional[str] = None
    viewport: Optional[Dict[str, int]] = None
    user_agent: Optional[str] = None
    headed: bool = False
    cookies: Optional[List[Dict[str, Any]]] = None
    wait_for_network_idle: Optional[Dict[str, Any]] = None


@dataclass
class MidsceneYamlScriptAndroidEnv:
    """Android环境配置"""
    device_id: Optional[str] = None
    app_package: Optional[str] = None
    app_activity: Optional[str] = None
    launch_app: bool = True


@dataclass
class MidsceneYamlScriptIOSEnv:
    """iOS环境配置"""
    udid: Optional[str] = None
    bundle_id: Optional[str] = None
    launch_app: bool = True


@dataclass
class MidsceneYamlScript:
    """YAML脚本
    
    完整的Midscene脚本定义
    """
    tasks: List[MidsceneYamlTask] = field(default_factory=list)
    web: Optional[MidsceneYamlScriptWebEnv] = None
    android: Optional[MidsceneYamlScriptAndroidEnv] = None
    ios: Optional[MidsceneYamlScriptIOSEnv] = None
    target: Optional[MidsceneYamlScriptWebEnv] = None  # deprecated, use web


def parse_yaml_script(content: str, source: str = "yaml") -> MidsceneYamlScript:
    """解析YAML脚本
    
    Args:
        content: YAML脚本内容
        source: 脚本来源标识
        
    Returns:
        解析后的MidsceneYamlScript对象
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML解析错误: {e}")
    
    if not data:
        return MidsceneYamlScript()
    
    # 解析任务列表
    tasks = []
    if 'tasks' in data and isinstance(data['tasks'], list):
        for task_data in data['tasks']:
            task = _parse_task(task_data)
            tasks.append(task)
    
    # 解析环境配置
    web_env = None
    if 'web' in data:
        web_env = _parse_web_env(data['web'])
    elif 'target' in data:
        web_env = _parse_web_env(data['target'])
    
    android_env = None
    if 'android' in data:
        android_env = _parse_android_env(data['android'])
    
    ios_env = None
    if 'ios' in data:
        ios_env = _parse_ios_env(data['ios'])
    
    return MidsceneYamlScript(
        tasks=tasks,
        web=web_env,
        android=android_env,
        ios=ios_env,
        target=web_env,  # 兼容旧版
    )


def _parse_task(data: Dict[str, Any]) -> MidsceneYamlTask:
    """解析单个任务"""
    name = data.get('name', 'Unnamed Task')
    continue_on_error = data.get('continueOnError', False)
    
    flow = []
    if 'flow' in data and isinstance(data['flow'], list):
        for item_data in data['flow']:
            item = _parse_flow_item(item_data)
            flow.append(item)
    
    return MidsceneYamlTask(
        name=name,
        flow=flow,
        continue_on_error=continue_on_error,
    )


def _parse_flow_item(data: Dict[str, Any]) -> MidsceneYamlFlowItem:
    """解析流程项"""
    return MidsceneYamlFlowItem(
        ai_act=data.get('aiAct') or data.get('ai_act'),
        ai_tap=data.get('aiTap') or data.get('ai_tap'),
        ai_hover=data.get('aiHover') or data.get('ai_hover'),
        ai_input=data.get('aiInput') or data.get('ai_input'),
        ai_keyboard_press=data.get('aiKeyboardPress') or data.get('ai_keyboard_press'),
        ai_scroll=data.get('aiScroll') or data.get('ai_scroll'),
        ai_assert=data.get('aiAssert') or data.get('ai_assert'),
        ai_wait_for=data.get('aiWaitFor') or data.get('ai_wait_for'),
        ai_query=data.get('aiQuery') or data.get('ai_query'),
        sleep=data.get('sleep'),
        log=data.get('log'),
    )


def _parse_web_env(data: Dict[str, Any]) -> MidsceneYamlScriptWebEnv:
    """解析Web环境配置"""
    return MidsceneYamlScriptWebEnv(
        url=data.get('url'),
        viewport=data.get('viewport'),
        user_agent=data.get('userAgent') or data.get('user_agent'),
        headed=data.get('headed', False),
        cookies=data.get('cookies'),
        wait_for_network_idle=data.get('waitForNetworkIdle') or data.get('wait_for_network_idle'),
    )


def _parse_android_env(data: Dict[str, Any]) -> MidsceneYamlScriptAndroidEnv:
    """解析Android环境配置"""
    return MidsceneYamlScriptAndroidEnv(
        device_id=data.get('deviceId') or data.get('device_id'),
        app_package=data.get('appPackage') or data.get('app_package'),
        app_activity=data.get('appActivity') or data.get('app_activity'),
        launch_app=data.get('launchApp', True),
    )


def _parse_ios_env(data: Dict[str, Any]) -> MidsceneYamlScriptIOSEnv:
    """解析iOS环境配置"""
    return MidsceneYamlScriptIOSEnv(
        udid=data.get('udid'),
        bundle_id=data.get('bundleId') or data.get('bundle_id'),
        launch_app=data.get('launchApp', True),
    )

"""
YAML模块测试
"""

import pytest

from mspy.core.yaml import parse_yaml_script
from mspy.core.yaml.parser import MidsceneYamlScript, MidsceneYamlTask


class TestYamlParser:
    """YAML解析器测试"""
    
    def test_parse_simple_script(self):
        """测试解析简单脚本"""
        yaml_content = """
web:
  url: https://example.com

tasks:
  - name: 测试任务
    flow:
      - aiTap: 登录按钮
"""
        script = parse_yaml_script(yaml_content, "test.yaml")
        
        assert script.web is not None
        assert script.web.url == "https://example.com"
        assert len(script.tasks) == 1
        assert script.tasks[0].name == "测试任务"
    
    def test_parse_script_with_agent_config(self):
        """测试解析带Agent配置的脚本"""
        yaml_content = """
web:
  url: https://example.com
  headless: true

agent:
  testId: my-test
  aiActContext: 这是一个测试页面

tasks:
  - name: 任务1
    flow:
      - ai: 点击登录按钮
"""
        script = parse_yaml_script(yaml_content, "test.yaml")
        
        assert script.agent is not None
        assert script.agent.test_id == "my-test"
        assert script.agent.ai_act_context == "这是一个测试页面"
    
    def test_parse_script_with_multiple_tasks(self):
        """测试解析多任务脚本"""
        yaml_content = """
web:
  url: https://example.com

tasks:
  - name: 任务1
    flow:
      - aiTap: 按钮1
  - name: 任务2
    continueOnError: true
    flow:
      - aiTap: 按钮2
      - aiAssert: 页面正常
"""
        script = parse_yaml_script(yaml_content, "test.yaml")
        
        assert len(script.tasks) == 2
        assert script.tasks[0].name == "任务1"
        assert script.tasks[1].name == "任务2"
        assert script.tasks[1].continue_on_error is True
    
    def test_parse_invalid_yaml(self):
        """测试解析无效YAML"""
        invalid_content = "this is not: valid: yaml: content"
        
        # 这应该能解析但结构可能不正确
        # 真正无效的YAML会抛出异常
        with pytest.raises(Exception):
            parse_yaml_script("invalid: [unclosed", "test.yaml")
    
    def test_parse_legacy_target_config(self):
        """测试解析旧版target配置"""
        yaml_content = """
target:
  url: https://legacy.example.com

tasks:
  - name: 旧版测试
    flow:
      - aiTap: 按钮
"""
        script = parse_yaml_script(yaml_content, "test.yaml")
        
        # target应该被解析
        assert script.target is not None or script.web is not None

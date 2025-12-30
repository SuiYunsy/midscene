"""
mspy 测试模块

运行方式: python -m pytest mspy/tests/test_basic.py -v
或者: cd mspy && python tests/test_basic.py
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import unittest


class TestSharedModule(unittest.TestCase):
    """测试shared模块"""
    
    def test_types_import(self):
        """测试类型导入"""
        from mspy.shared.types import Point, Size, Rect
        
        point = Point(left=10, top=20)
        self.assertEqual(point.left, 10)
        self.assertEqual(point.top, 20)
        
        size = Size(width=100, height=200)
        self.assertEqual(size.width, 100)
        self.assertEqual(size.height, 200)
    
    def test_logger(self):
        """测试日志模块"""
        from mspy.shared.logger import get_debug, get_logger
        
        debug = get_debug('test')
        self.assertIsNotNone(debug)
        
        logger = get_logger('test')
        self.assertIsNotNone(logger)
    
    def test_utils(self):
        """测试工具函数"""
        from mspy.shared.utils import assert_condition, generate_id, get_timestamp
        
        # 测试assert
        assert_condition(True, "应该通过")
        
        with self.assertRaises(AssertionError):
            assert_condition(False, "应该失败")
        
        # 测试ID生成
        id1 = generate_id()
        id2 = generate_id()
        self.assertNotEqual(id1, id2)
        
        # 测试时间戳
        ts = get_timestamp()
        self.assertIsInstance(ts, int)
        self.assertGreater(ts, 0)
    
    def test_env_config(self):
        """测试环境配置"""
        from mspy.shared.env import ModelConfigManager, GlobalConfigManager
        
        global_manager = GlobalConfigManager()
        self.assertIsNotNone(global_manager)
        
        model_manager = ModelConfigManager()
        self.assertIsNotNone(model_manager)


class TestCoreModule(unittest.TestCase):
    """测试core模块"""
    
    def test_types_import(self):
        """测试核心类型导入"""
        from mspy.core.types import (
            UIContext,
            ServiceError,
            ExecutionTask,
            GroupedActionDump,
        )
        
        # 类型应该可以导入
        self.assertIsNotNone(UIContext)
        self.assertIsNotNone(ServiceError)
    
    def test_agent_import(self):
        """测试Agent导入"""
        from mspy.core.agent import Agent, AgentOpt
        
        self.assertIsNotNone(Agent)
        self.assertIsNotNone(AgentOpt)
    
    def test_yaml_parser(self):
        """测试YAML解析"""
        from mspy.core.yaml import parse_yaml_script
        
        yaml_content = """
web:
  url: https://example.com
  headed: true

tasks:
  - name: 测试任务
    flow:
      - aiTap: 登录按钮
      - aiInput:
          locate: 用户名输入框
          value: test
      - sleep: 1000
"""
        
        script = parse_yaml_script(yaml_content)
        
        self.assertEqual(len(script.tasks), 1)
        self.assertEqual(script.tasks[0].name, '测试任务')
        self.assertEqual(len(script.tasks[0].flow), 3)
        self.assertEqual(script.web.url, 'https://example.com')
        self.assertTrue(script.web.headed)


class TestWebModule(unittest.TestCase):
    """测试web模块"""
    
    def test_web_page_import(self):
        """测试Web页面导入"""
        from mspy.web.web_page import AbstractWebPage
        from mspy.web.web_element import WebElementInfo
        
        self.assertIsNotNone(AbstractWebPage)
        self.assertIsNotNone(WebElementInfo)
    
    def test_playwright_agent_import(self):
        """测试PlaywrightAgent导入"""
        from mspy.web.playwright import PlaywrightAgent, WebPage
        
        self.assertIsNotNone(PlaywrightAgent)
        self.assertIsNotNone(WebPage)


class TestCLIModule(unittest.TestCase):
    """测试cli模块"""
    
    def test_batch_runner_import(self):
        """测试批量执行器导入"""
        from mspy.cli.batch_runner import BatchRunner, BatchRunnerConfig
        
        config = BatchRunnerConfig(
            files=['test.yaml'],
            concurrent=1,
        )
        
        self.assertEqual(config.files, ['test.yaml'])
        self.assertEqual(config.concurrent, 1)
    
    def test_config_factory(self):
        """测试配置工厂"""
        from mspy.cli.config import create_files_config
        
        self.assertIsNotNone(create_files_config)


if __name__ == '__main__':
    print("=== mspy 单元测试 ===\n")
    unittest.main(verbosity=2)

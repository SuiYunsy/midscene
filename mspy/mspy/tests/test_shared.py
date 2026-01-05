"""
共享模块测试
"""

import os
import pytest

from mspy.shared.utils import uuid, generate_hash_id, assert_condition
from mspy.shared.common import get_midscene_run_dir, get_midscene_run_sub_dir
from mspy.shared.types import Point, Size, Rect


class TestUtils:
    """工具函数测试"""
    
    def test_uuid(self):
        """测试UUID生成"""
        id1 = uuid()
        id2 = uuid()
        
        assert id1 != id2
        assert len(id1) > 0
    
    def test_generate_hash_id(self):
        """测试哈希ID生成"""
        rect = {"left": 0, "top": 0, "width": 100, "height": 50}
        id1 = generate_hash_id(rect, "test")
        id2 = generate_hash_id(rect, "test")
        
        assert id1 == id2  # 相同输入应产生相同输出
        assert len(id1) >= 5
    
    def test_generate_hash_id_different_input(self):
        """测试不同输入产生不同哈希"""
        rect1 = {"left": 0, "top": 0, "width": 100, "height": 50}
        rect2 = {"left": 10, "top": 10, "width": 100, "height": 50}
        
        id1 = generate_hash_id(rect1, "test")
        id2 = generate_hash_id(rect2, "test")
        
        assert id1 != id2
    
    def test_assert_condition_pass(self):
        """测试断言通过"""
        # 不应抛出异常
        assert_condition(True, "Should pass")
        assert_condition(1, "Should pass")
        assert_condition("non-empty", "Should pass")
    
    def test_assert_condition_fail(self):
        """测试断言失败"""
        with pytest.raises(AssertionError, match="Custom message"):
            assert_condition(False, "Custom message")
        
        with pytest.raises(AssertionError):
            assert_condition(None)


class TestCommon:
    """通用功能测试"""
    
    def test_get_midscene_run_dir(self):
        """测试获取运行目录名称"""
        dir_name = get_midscene_run_dir()
        assert dir_name == "midscene_run"
    
    def test_get_midscene_run_sub_dir(self):
        """测试获取运行子目录"""
        import shutil
        
        # 获取子目录
        dump_dir = get_midscene_run_sub_dir("dump")
        
        assert dump_dir.endswith("dump")
        assert os.path.isdir(dump_dir)
        
        # 清理测试目录
        base_dir = os.path.dirname(dump_dir)
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)


class TestTypes:
    """类型测试"""
    
    def test_point(self):
        """测试Point类型"""
        point = Point(left=10.5, top=20.3)
        assert point.left == 10.5
        assert point.top == 20.3
    
    def test_size(self):
        """测试Size类型"""
        size = Size(width=1920, height=1080)
        assert size.width == 1920
        assert size.height == 1080
        assert size.dpr is None
    
    def test_rect(self):
        """测试Rect类型"""
        rect = Rect(left=0, top=0, width=100, height=50)
        assert rect.left == 0
        assert rect.top == 0
        assert rect.width == 100
        assert rect.height == 50
        assert rect.zoom is None

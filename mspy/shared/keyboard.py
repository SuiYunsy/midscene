"""
美式键盘布局定义

从 packages/shared/src/us-keyboard-layout.ts 迁移
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class KeyDefinition:
    """键定义"""
    key: str
    key_code: int
    code: str
    text: Optional[str] = None
    shifted_key: Optional[str] = None
    shift_key_code: Optional[int] = None
    location: int = 0


# 键定义字典
KEY_DEFINITIONS: dict[str, KeyDefinition] = {
    # 功能键
    "Escape": KeyDefinition(key="Escape", key_code=27, code="Escape"),
    "Tab": KeyDefinition(key="Tab", key_code=9, code="Tab", text="\t"),
    "Enter": KeyDefinition(key="Enter", key_code=13, code="Enter", text="\r"),
    "Backspace": KeyDefinition(key="Backspace", key_code=8, code="Backspace"),
    "Delete": KeyDefinition(key="Delete", key_code=46, code="Delete"),
    "Insert": KeyDefinition(key="Insert", key_code=45, code="Insert"),
    "Home": KeyDefinition(key="Home", key_code=36, code="Home"),
    "End": KeyDefinition(key="End", key_code=35, code="End"),
    "PageUp": KeyDefinition(key="PageUp", key_code=33, code="PageUp"),
    "PageDown": KeyDefinition(key="PageDown", key_code=34, code="PageDown"),
    
    # 箭头键
    "ArrowUp": KeyDefinition(key="ArrowUp", key_code=38, code="ArrowUp"),
    "ArrowDown": KeyDefinition(key="ArrowDown", key_code=40, code="ArrowDown"),
    "ArrowLeft": KeyDefinition(key="ArrowLeft", key_code=37, code="ArrowLeft"),
    "ArrowRight": KeyDefinition(key="ArrowRight", key_code=39, code="ArrowRight"),
    
    # 修饰键
    "Shift": KeyDefinition(key="Shift", key_code=16, code="ShiftLeft", location=1),
    "ShiftLeft": KeyDefinition(key="Shift", key_code=16, code="ShiftLeft", location=1),
    "ShiftRight": KeyDefinition(key="Shift", key_code=16, code="ShiftRight", location=2),
    "Control": KeyDefinition(key="Control", key_code=17, code="ControlLeft", location=1),
    "ControlLeft": KeyDefinition(key="Control", key_code=17, code="ControlLeft", location=1),
    "ControlRight": KeyDefinition(key="Control", key_code=17, code="ControlRight", location=2),
    "Alt": KeyDefinition(key="Alt", key_code=18, code="AltLeft", location=1),
    "AltLeft": KeyDefinition(key="Alt", key_code=18, code="AltLeft", location=1),
    "AltRight": KeyDefinition(key="Alt", key_code=18, code="AltRight", location=2),
    "Meta": KeyDefinition(key="Meta", key_code=91, code="MetaLeft", location=1),
    "MetaLeft": KeyDefinition(key="Meta", key_code=91, code="MetaLeft", location=1),
    "MetaRight": KeyDefinition(key="Meta", key_code=92, code="MetaRight", location=2),
    
    # F键
    "F1": KeyDefinition(key="F1", key_code=112, code="F1"),
    "F2": KeyDefinition(key="F2", key_code=113, code="F2"),
    "F3": KeyDefinition(key="F3", key_code=114, code="F3"),
    "F4": KeyDefinition(key="F4", key_code=115, code="F4"),
    "F5": KeyDefinition(key="F5", key_code=116, code="F5"),
    "F6": KeyDefinition(key="F6", key_code=117, code="F6"),
    "F7": KeyDefinition(key="F7", key_code=118, code="F7"),
    "F8": KeyDefinition(key="F8", key_code=119, code="F8"),
    "F9": KeyDefinition(key="F9", key_code=120, code="F9"),
    "F10": KeyDefinition(key="F10", key_code=121, code="F10"),
    "F11": KeyDefinition(key="F11", key_code=122, code="F11"),
    "F12": KeyDefinition(key="F12", key_code=123, code="F12"),
    
    # 空格
    " ": KeyDefinition(key=" ", key_code=32, code="Space", text=" "),
    "Space": KeyDefinition(key=" ", key_code=32, code="Space", text=" "),
    
    # 数字行
    "0": KeyDefinition(key="0", key_code=48, code="Digit0", text="0", shifted_key=")"),
    "1": KeyDefinition(key="1", key_code=49, code="Digit1", text="1", shifted_key="!"),
    "2": KeyDefinition(key="2", key_code=50, code="Digit2", text="2", shifted_key="@"),
    "3": KeyDefinition(key="3", key_code=51, code="Digit3", text="3", shifted_key="#"),
    "4": KeyDefinition(key="4", key_code=52, code="Digit4", text="4", shifted_key="$"),
    "5": KeyDefinition(key="5", key_code=53, code="Digit5", text="5", shifted_key="%"),
    "6": KeyDefinition(key="6", key_code=54, code="Digit6", text="6", shifted_key="^"),
    "7": KeyDefinition(key="7", key_code=55, code="Digit7", text="7", shifted_key="&"),
    "8": KeyDefinition(key="8", key_code=56, code="Digit8", text="8", shifted_key="*"),
    "9": KeyDefinition(key="9", key_code=57, code="Digit9", text="9", shifted_key="("),
    
    # 字母键
    "a": KeyDefinition(key="a", key_code=65, code="KeyA", text="a", shifted_key="A"),
    "b": KeyDefinition(key="b", key_code=66, code="KeyB", text="b", shifted_key="B"),
    "c": KeyDefinition(key="c", key_code=67, code="KeyC", text="c", shifted_key="C"),
    "d": KeyDefinition(key="d", key_code=68, code="KeyD", text="d", shifted_key="D"),
    "e": KeyDefinition(key="e", key_code=69, code="KeyE", text="e", shifted_key="E"),
    "f": KeyDefinition(key="f", key_code=70, code="KeyF", text="f", shifted_key="F"),
    "g": KeyDefinition(key="g", key_code=71, code="KeyG", text="g", shifted_key="G"),
    "h": KeyDefinition(key="h", key_code=72, code="KeyH", text="h", shifted_key="H"),
    "i": KeyDefinition(key="i", key_code=73, code="KeyI", text="i", shifted_key="I"),
    "j": KeyDefinition(key="j", key_code=74, code="KeyJ", text="j", shifted_key="J"),
    "k": KeyDefinition(key="k", key_code=75, code="KeyK", text="k", shifted_key="K"),
    "l": KeyDefinition(key="l", key_code=76, code="KeyL", text="l", shifted_key="L"),
    "m": KeyDefinition(key="m", key_code=77, code="KeyM", text="m", shifted_key="M"),
    "n": KeyDefinition(key="n", key_code=78, code="KeyN", text="n", shifted_key="N"),
    "o": KeyDefinition(key="o", key_code=79, code="KeyO", text="o", shifted_key="O"),
    "p": KeyDefinition(key="p", key_code=80, code="KeyP", text="p", shifted_key="P"),
    "q": KeyDefinition(key="q", key_code=81, code="KeyQ", text="q", shifted_key="Q"),
    "r": KeyDefinition(key="r", key_code=82, code="KeyR", text="r", shifted_key="R"),
    "s": KeyDefinition(key="s", key_code=83, code="KeyS", text="s", shifted_key="S"),
    "t": KeyDefinition(key="t", key_code=84, code="KeyT", text="t", shifted_key="T"),
    "u": KeyDefinition(key="u", key_code=85, code="KeyU", text="u", shifted_key="U"),
    "v": KeyDefinition(key="v", key_code=86, code="KeyV", text="v", shifted_key="V"),
    "w": KeyDefinition(key="w", key_code=87, code="KeyW", text="w", shifted_key="W"),
    "x": KeyDefinition(key="x", key_code=88, code="KeyX", text="x", shifted_key="X"),
    "y": KeyDefinition(key="y", key_code=89, code="KeyY", text="y", shifted_key="Y"),
    "z": KeyDefinition(key="z", key_code=90, code="KeyZ", text="z", shifted_key="Z"),
}


def get_key_definition(key: str) -> Optional[KeyDefinition]:
    """
    获取键定义
    
    Args:
        key: 键名称
    
    Returns:
        KeyDefinition或None
    """
    # 先尝试直接匹配
    if key in KEY_DEFINITIONS:
        return KEY_DEFINITIONS[key]
    
    # 尝试小写匹配
    lower_key = key.lower()
    if lower_key in KEY_DEFINITIONS:
        return KEY_DEFINITIONS[lower_key]
    
    return None


def parse_key_combination(key_string: str) -> list[str]:
    """
    解析键组合
    
    Args:
        key_string: 键组合字符串，如 "Control+A" 或 "Shift+Enter"
    
    Returns:
        键列表
    """
    return [k.strip() for k in key_string.split("+")]

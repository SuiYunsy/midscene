"""Constants for Midscene."""

from enum import Enum

# Text size thresholds
TEXT_SIZE_THRESHOLD = 9
TEXT_MAX_SIZE = 40

# Container minimum dimensions
CONTAINER_MINI_HEIGHT = 3
CONTAINER_MINI_WIDTH = 3


class NodeType(str, Enum):
    """Node types for web elements."""
    
    CONTAINER = "CONTAINER Node"
    FORM_ITEM = "FORM_ITEM Node"
    BUTTON = "BUTTON Node"
    A = "Anchor Node"
    IMG = "IMG Node"
    TEXT = "TEXT Node"
    POSITION = "POSITION Node"


# Server ports
PLAYGROUND_SERVER_PORT = 5800
SCRCPY_SERVER_PORT = 5700

# WebDriver constants
WEBDRIVER_ELEMENT_ID_KEY = "element-6066-11e4-a52e-4f735466cecf"
DEFAULT_WDA_PORT = 8100

# Wait timeouts
DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT = 5000
DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT = 2000
DEFAULT_WAIT_FOR_NETWORK_IDLE_TIME = 300
DEFAULT_WAIT_FOR_NETWORK_IDLE_CONCURRENCY = 2

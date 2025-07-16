# 虛擬報價機模組
# Virtual Quote Machine Module
# 
# 提供與群益API相同介面的虛擬報價機，用於測試simple_integrated.py
# 
# 版本: v1.0
# 作者: AI Assistant
# 日期: 2025-01-13

__version__ = "1.0.0"
__author__ = "AI Assistant"
__description__ = "Virtual Quote Machine for simple_integrated.py testing"

# 模組導入
from .Global import *
from .quote_engine import VirtualQuoteEngine
from .event_dispatcher import EventDispatcher
from .order_simulator import OrderSimulator
from .config_manager import ConfigManager

# 版本信息
def get_version():
    return __version__

def get_info():
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__
    }

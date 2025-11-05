"""
MemoryStack - The Open-Source Intelligence Layer for LLM Memory

Cut your LLM costs by 77%. Give your AI perfect memory. In 30 seconds.
"""

__version__ = "3.0.0"
__author__ = "João Lucas"
__license__ = "MIT"

from .main import app
from .config import settings

__all__ = ["app", "settings"]

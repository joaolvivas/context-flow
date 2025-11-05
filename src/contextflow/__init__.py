"""
ContextFlow - The Open-Source AI Memory Proxy

Self-hosted, invisible, and works with any tool that lets you customize the API endpoint.
Cuts LLM costs by 77% through intelligent context management.
"""

__version__ = "3.0.0"
__author__ = "João Lucas"
__license__ = "MIT"

from .main import app
from .config import settings

__all__ = ["app", "settings"]

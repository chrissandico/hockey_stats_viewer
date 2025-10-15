"""
Minimal Mobile Cache Service for testing
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any

class ConnectionType(Enum):
    WIFI = "wifi"
    CELLULAR_4G = "4g"
    OFFLINE = "offline"

class DataPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class ConnectionProfile:
    connection_type: ConnectionType
    bandwidth_kbps: int
    latency_ms: int
    is_metered: bool

class MobileCacheService:
    def __init__(self):
        self.current_connection = ConnectionProfile(
            ConnectionType.WIFI, 0, 0, False
        )
        self.stats = {'test': 'value'}
    
    def get_mobile_cache_stats(self) -> Dict[str, Any]:
        return self.stats
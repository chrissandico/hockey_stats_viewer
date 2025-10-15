#!/usr/bin/env python3
import sys
sys.path.append('hockey_stats_webapp')

try:
    print("Testing imports...")
    
    # Test individual imports
    print("1. Testing enum import...")
    from enum import Enum
    print("   ✓ enum imported")
    
    print("2. Testing dataclass import...")
    from dataclasses import dataclass, field
    print("   ✓ dataclass imported")
    
    print("3. Testing datetime import...")
    from datetime import datetime, timedelta
    print("   ✓ datetime imported")
    
    print("4. Testing collections import...")
    from collections import defaultdict, deque
    print("   ✓ collections imported")
    
    print("5. Testing smart cache manager import...")
    from services.smart_cache_manager import SmartCacheManager
    print("   ✓ SmartCacheManager imported")
    
    print("6. Testing multi level cache import...")
    from services.multi_level_cache import MultiLevelCache
    print("   ✓ MultiLevelCache imported")
    
    print("7. Testing mobile cache service import...")
    import services.mobile_cache_service
    print("   ✓ Module imported")
    
    print("8. Checking module contents...")
    print(f"   Module attributes: {[attr for attr in dir(services.mobile_cache_service) if not attr.startswith('_')]}")
    
    print("9. Testing direct execution...")
    exec(open('hockey_stats_webapp/services/mobile_cache_service.py').read())
    print("   ✓ Direct execution successful")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
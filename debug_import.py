#!/usr/bin/env python3
import sys
sys.path.append('hockey_stats_webapp')

try:
    import services.mobile_cache_service as mcs
    print("Module imported successfully")
    print("Available attributes:", dir(mcs))
    
    # Try to access the class
    if hasattr(mcs, 'MobileCacheService'):
        print("MobileCacheService class found")
    else:
        print("MobileCacheService class NOT found")
        
    # Check for other classes
    for attr in dir(mcs):
        if not attr.startswith('_'):
            obj = getattr(mcs, attr)
            if isinstance(obj, type):
                print(f"Found class: {attr}")
                
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
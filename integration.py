import sys, os
from pathlib import Path
IS_WINDOWS=sys.platform=='win32'
STORE_BUILD=getattr(sys,'frozen',False) and 'windowsapps' in str(Path(sys.executable)).lower()
if IS_WINDOWS:
    from platform_adapters.windows import register, unregister
else:
    from platform_adapters.linux import register, unregister

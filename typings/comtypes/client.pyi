# Type hints for comtypes.client
from typing import Any, Optional

def GetModule(tlib: str) -> Any: ...
def CreateObject(clsid: Any, interface: Optional[Any] = None) -> Any: ...

gen_dir: str

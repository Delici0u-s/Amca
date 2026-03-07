VERSION_MAP = {
    None    : "v1",
    "2.0.1" : "v2_0_1",
    "bunny" : "template",
}

import re
from typing import Optional

def meson_get_val(meson_file, var_name) -> Optional[str]:
    pat = re.compile(rf"^{var_name}\s*=\s*['\"](.*)['\"]")
    
    for line in (meson_file).read_text().splitlines():
        m = pat.match(line)
        if m:
            return m.group(1)
    return None


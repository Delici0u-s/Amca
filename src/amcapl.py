import impl.amcapl_main as im
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.argv[0] = str(Path(sys.executable).resolve())
    sys.exit(im.main())

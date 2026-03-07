import impl.amcapl_main as im
import sys
from pathlib import Path

if __name__ == "__main__":
    try:
        # sys.argv[0] = str(Path(sys.executable).resolve())
        sys.argv[0] = __file__
        sys.exit(im.main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    # except KeyboardInterrupt:
    #     sys.exit(130)

from impl.main import main
import sys

if __name__ == "__main__":
    sys.argv[0] = __file__  # as abspath
    exit(main())

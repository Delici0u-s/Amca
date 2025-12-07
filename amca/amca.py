import src.amca_impl as amca_impl
import sys

if __name__ == "__main__":
    sys.argv[0] = __file__  # as abspath
    exit(amca_impl.main())

from impl.amca.dirparse import DirInfo, DirParser
from impl.arging.argparse import parse_args
from impl.arging.arg_eval import arg_eval


def run(meson_root_dir_info: DirInfo, dir_parser: DirParser, args: list[str]):

    """
    Entrypoint where the plugin starts.
    """
    opts = parse_args(args)
    arg_eval(opts, meson_root_dir_info, dir_parser, args)

    return opts



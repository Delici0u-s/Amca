from impl.amca.dirparse import DirInfo, DirParser
from impl.util.argparse import parse_args


def run(meson_root_dir_info: DirInfo, dir_parser: DirParser, args: list[str]):
    """
    Entrypoint where the plugin starts.
    """
    print("Meson directory detected, args: ", args)
    opts = parse_args(args)

    # quick debug dump (feel free to remove in production)
    print("Parsed options:")
    for k, v in sorted(vars(opts).items()):
        print(f"  {k}: {v}")

    # Example of how you might use opts (pseudocode outline):
    # if opts.mode is None:
    #   # run default pipeline: setup -> maybe reconfigure -> compile -> execute
    # else:
    #   # run the selected single mode
    #
    # Respect opts.skip_reconf / opts.skip_compile / opts.skip_exec when composing pipeline.
    # Respect opts.clear / opts.wipe (and ensure you check opts.force before performing a wipe).
    #
    # Note: this function returns after parsing for now; integrate actual task execution below.

    return opts


# def run(meson_root_dir_info: DirInfo, dir_parser: DirParser, args: list[str]):
#
#     print("Meson directory detected")

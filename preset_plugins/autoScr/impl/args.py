import argparse
from dataclasses import dataclass

from impl.constants import VERBOSE_FLAG


@dataclass(slots=True)
class ParsedArgs:
  verbose: bool
  assume_yes: bool
  forwarded_args: list[str]


def parse_args(args: list[str]) -> ParsedArgs:
  parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
  parser.add_argument("-y", "--y", "--yes", action="store_true", dest="yes")
  parser.add_argument(VERBOSE_FLAG, action="store_true", dest="verbose")

  parsed, remaining = parser.parse_known_args(args)

  return ParsedArgs(
    verbose=parsed.verbose,
    assume_yes=parsed.yes,
    forwarded_args=remaining,  # everything else forwarded to script
  )

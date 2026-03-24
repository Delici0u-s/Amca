import argparse
from dataclasses import dataclass

from impl.constants import VERBOSE_FLAG


@dataclass(slots=True)
class ParsedArgs:
  verbose: bool
  assume_yes: bool
  create_new: bool
  forwarded_args: list[str]


def should_create_new(args: list[str]) -> bool:
  return any(a in ("n", "new") for a in args)


def parse_args(args: list[str]) -> ParsedArgs:
  parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
  parser.add_argument("-y", "--y", "--yes", action="store_true", dest="yes")
  parser.add_argument(VERBOSE_FLAG, action="store_true", dest="verbose")

  parsed, remaining = parser.parse_known_args(args)

  forwarded = [a for a in remaining if a not in ("n", "new")]
  create_new = should_create_new(remaining)

  return ParsedArgs(
    verbose=parsed.verbose,
    assume_yes=parsed.yes,
    create_new=create_new,
    forwarded_args=forwarded,
  )

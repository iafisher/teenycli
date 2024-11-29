import argparse
import enum
import os
import subprocess
import sys
from typing import Any, Callable, NoReturn, Optional


_Handler = Callable[[argparse.Namespace], Any]


class Args(enum.Enum):
    ONE = enum.auto()
    AT_LEAST_ONE = enum.auto()
    ZERO_OR_MORE = enum.auto()


class ArgP:
    _DISPATCH_NAME = "_teenycli_handler"

    def __init__(
        self,
        *,
        description: Optional[str] = None,
        version: Optional[str] = None,
        _internal_parser=None,
    ):
        if _internal_parser is not None:
            self.parser = _internal_parser
        else:
            self.parser = argparse.ArgumentParser(description=description)
            self.parser.set_defaults(**{self._DISPATCH_NAME: None})

            if version is not None:
                self.parser.add_argument("--version", action="version", version=version)

        self.subparsers = None

    def switch(self, name: str, *, help=None, metavar=None) -> None:
        self.parser.add_argument(name, action="store_true", help=help, metavar=metavar)

    def arg(
        self,
        name: str,
        *,
        n: Args = Args.ONE,
        required: bool = True,
        choices=None,
        type=None,
        help=None,
        metavar=None,
    ) -> None:
        if n == Args.ONE:
            if required:
                self.parser.add_argument(
                    name, choices=choices, type=type, help=help, metavar=metavar
                )
            else:
                self.parser.add_argument(name, nargs="?")
        elif n == Args.AT_LEAST_ONE:
            self.parser.add_argument(
                name, nargs="+", choices=choices, type=type, help=help, metavar=metavar
            )
        elif n == Args.ZERO_OR_MORE:
            self.parser.add_argument(
                name, nargs="*", choices=choices, type=type, help=help, metavar=metavar
            )
        else:
            raise TeenyCliError(
                f"unexpected value of `n` passed to `{self.__class__.__name__}.arg()`: {n!r}"
            )

    def subcmd(self, name: str, handler: _Handler, *, help=None) -> "ArgP":
        if self.subparsers is None:
            self.subparsers = self.parser.add_subparsers(
                title="subcommands", metavar=""
            )

        parser = self.subparsers.add_parser(name, description=help, help=help)  # type: ignore
        parser.set_defaults(**{self._DISPATCH_NAME: handler})
        return ArgP(_internal_parser=parser)

    def dispatch(self, handler: Optional[_Handler] = None, *, argv=None) -> None:
        args = self.parser.parse_args(argv)
        configured_handler = getattr(args, self._DISPATCH_NAME)
        if configured_handler is None:
            if handler is None:
                if self.subparsers is not None:
                    self.parser.print_help()
                    sys.exit(1)
                else:
                    raise TeenyCliError(
                        f"You need to either pass a handler to `{self.__class__.__name__}.dispatch()`, "
                        + "or register subcommands with `subcmd()`."
                    )

            handler(args)
        else:
            configured_handler(args)


def confirm(message: str) -> None:
    message = message.rstrip() + " "

    while True:
        yesno = input(message).strip().lower()
        if yesno in {"yes", "y"}:
            return
        elif yesno in {"no", "n"}:
            sys.exit(2)
        else:
            continue


def shell(cmd) -> str:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
    return proc.stdout


def error(msg: str) -> None:
    print(f"{red('Error')}: {msg}", file=sys.stderr)


def bail(msg: str) -> NoReturn:
    error(msg)
    sys.exit(1)


def warn(msg: str) -> None:
    print(f"{yellow('Warning')}: {msg}", file=sys.stderr)


def red(s: str) -> str:
    return _colored(s, 31)


def yellow(s: str) -> str:
    return _colored(s, 33)


def cyan(s: str) -> str:
    return _colored(s, 36)


def green(s: str) -> str:
    return _colored(s, 32)


def _colored(s: str, code: int) -> str:
    if not _has_color():
        return s

    return f"\033[{code}m{s}\033[0m"


# don't access directly; use _has_color() instead
#
# once set, this may be reset back to `None` if the module is re-imported elsewhere
_COLOR = None


def _has_color() -> bool:
    global _COLOR

    if _COLOR is not None:
        return _COLOR

    _COLOR = not (
        # https://no-color.org/
        "NO_COLOR" in os.environ
        or not os.isatty(sys.stdout.fileno())
        or not os.isatty(sys.stderr.fileno())
    )

    return _COLOR


class TeenyCliError(Exception):
    pass

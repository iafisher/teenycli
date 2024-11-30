import argparse
import os
import subprocess
import sys
from typing import Any, Callable, NoReturn, Optional


_Handler = Callable[[argparse.Namespace], Any]


class ArgP:
    _DISPATCH_NAME = "_teenycli_handler"

    ZERO = "zero"
    ONE = "one"
    MANY = "many"

    def __init__(
        self,
        *,
        version: Optional[str] = None,
        _internal_parser=None,
        **kwargs,
    ):
        if _internal_parser is not None:
            self.parser = _internal_parser
        else:
            self.parser = argparse.ArgumentParser(**kwargs)
            self.parser.set_defaults(**{self._DISPATCH_NAME: None})

            if version is not None:
                self.parser.add_argument("--version", action="version", version=version)

        self.subparsers = None

    def add(
        self,
        *names,
        n: Optional[str] = None,
        required: Optional[bool] = None,
        **kwargs,
    ) -> "ArgP":
        _assert(len(names) >= 1, "You need to pass at least one name to `add()`.")
        is_flag = names[0].startswith("-")

        if n == self.ZERO and not is_flag:
            raise TeenyCliError(
                "`arg=ZERO` is invalid for positional arguments. "
                + "Start the name with a hyphen to make it a flag, "
                + "or else change `arg` to `ONE` or `MANY`."
            )

        if n == self.ZERO and required:
            raise TeenyCliError("`arg=ZERO` and `required=True` are incompatible.")

        if "default" in kwargs:
            if required:
                raise TeenyCliError(
                    "`required=True` is incompatible with passing `default`."
                )

            default = kwargs.pop("default")
            required = False
        else:
            default = [] if n == self.MANY else None

        if n is None:
            n = self.ZERO if is_flag and required is None else self.ONE

        if required is None:
            required = not is_flag

        if n == self.ZERO:
            # argparse won't accept `nargs=None` if `action="store_true"`.
            self.parser.add_argument(*names, action="store_true", **kwargs)
            return self

        nargs: Optional[str]
        if n == self.MANY:
            nargs = "+" if is_flag or required else "*"
        elif n == self.ONE:
            nargs = "?" if not required and not is_flag else None
        else:
            nargs = None

        default = kwargs.pop("default", [] if n == self.MANY else None)
        if is_flag:
            self.parser.add_argument(
                *names, nargs=nargs, required=required, default=default, **kwargs
            )
        else:
            # argparse won't accept `required=None` at all for positionals.
            self.parser.add_argument(*names, nargs=nargs, default=default, **kwargs)

        return self

    def subcmd(
        self, name: str, handler: _Handler, *, help: Optional[str] = None
    ) -> "ArgP":
        if self.subparsers is None:
            self.subparsers = self.parser.add_subparsers(
                title="subcommands", metavar=""
            )

        parser = self.subparsers.add_parser(name, description=help, help=help)  # type: ignore
        parser.set_defaults(**{self._DISPATCH_NAME: handler})
        return ArgP(_internal_parser=parser)

    def parse(self, argv=None) -> argparse.Namespace:
        return self.parser.parse_args(argv)

    def dispatch(self, handler: Optional[_Handler] = None, *, argv=None) -> Any:
        args = self.parser.parse_args(argv)
        print(args)
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

            return handler(args)
        else:
            return configured_handler(args)


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


def _assert(cond: bool, message: str) -> None:
    if not cond:
        raise TeenyCliError(message)

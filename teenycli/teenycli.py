import argparse
import os
import re
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
        self.has_positionals = False

    def add(
        self,
        *names,
        n: Optional[str] = None,
        required: Optional[bool] = None,
        **kwargs,
    ) -> "ArgP":
        if len(names) == 0:
            raise TeenyCliError("You need to pass at least one name to `add()`.")

        is_flag = names[0].startswith("-")

        if n == self.ZERO and not is_flag:
            raise TeenyCliError(
                "`arg=ZERO` is invalid for positional arguments. "
                + "Start the name with a hyphen to make it a flag, "
                + "or else change `arg` to `ONE` or `MANY`."
            )

        if n == self.ZERO and required:
            raise TeenyCliError("`arg=ZERO` and `required=True` are incompatible.")

        if not is_flag and self.subparsers is not None:
            self._no_subcommands_and_positionals()

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

        if is_flag:
            self.parser.add_argument(
                *names, nargs=nargs, required=required, default=default, **kwargs
            )
        else:
            # argparse won't accept `required=None` at all for positionals.
            self.parser.add_argument(*names, nargs=nargs, default=default, **kwargs)
            self.has_positionals = True

        return self

    def subcmd(
        self,
        name: str,
        handler: _Handler,
        *,
        help: Optional[str] = None,
        required: Optional[bool] = None,
    ) -> "ArgP":
        if self.has_positionals:
            self._no_subcommands_and_positionals()

        if self.subparsers is None:
            self.subparsers = self.parser.add_subparsers(
                title="subcommands",
                metavar="",
                required=(required if required is not None else True),
            )
        else:
            # It's annoying that the API makes it possible. A more explicit API might look like:
            #
            #   subcmds = argp.subcmds(required=False)
            #   subcmds.add("whatever", handler)
            #
            # But this is more verbose and introduces a new `subcmds` object. I expect that most
            # users will want required subcommands, so I chose the more concise API.
            if required is not None:
                raise TeenyCliError(
                    "The `required` parameter must be specified exactly once, "
                    + "on the first invocation of `subcmd()`."
                )

        parser = self.subparsers.add_parser(name, description=help, help=help)  # type: ignore
        parser.set_defaults(**{self._DISPATCH_NAME: handler})
        return ArgP(_internal_parser=parser)

    def parse(self, argv=None) -> argparse.Namespace:
        return self.parser.parse_args(argv)

    def dispatch(self, handler: Optional[_Handler] = None, *, argv=None) -> Any:
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

            return handler(args)
        else:
            return configured_handler(args)

    def _no_subcommands_and_positionals(self):
        raise TeenyCliError(
            "A parser with subcommands cannot also have positional arguments."
        )


_ansi_codes_re = re.compile(r"\033\[[;?0-9]*[a-zA-Z]")


def print_(message: str, file=None, **kwargs):
    not_a_terminal = not _isatty(file if file is not None else sys.stdout)
    # https://no-color.org/
    if not_a_terminal or "NO_COLOR" in os.environ:
        message = _ansi_codes_re.sub(message, "")

    print(message, file=file, **kwargs)


def _isatty(stream):
    try:
        return stream.isatty()
    except Exception:
        return False


def confirm(message: str) -> bool:
    message = message.rstrip() + " "

    while True:
        yesno = input(message).strip().lower()
        if yesno in {"yes", "y"}:
            return True
        elif yesno in {"no", "n"}:
            return False
        else:
            print("Please respond 'yes' or 'no'.")
            continue


def confirm_or_bail(message: str, *, exit_code: int = 2) -> None:
    r = confirm(message)
    if not r:
        sys.exit(exit_code)


def run(cmd, *, shell: bool = False) -> str:
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, text=True, check=True, shell=shell
        )
        return proc.stdout
    except subprocess.CalledProcessError as e:
        raise TeenyCliError(str(e)) from None


def error(msg: str) -> None:
    print_(f"{red('Error')}: {msg}", file=sys.stderr)


def bail(msg: str, *, code: int = 2) -> NoReturn:
    error(msg)
    sys.exit(code)


def warn(msg: str) -> None:
    print_(f"{yellow('Warning')}: {msg}", file=sys.stderr)


def red(s: str) -> str:
    return _colored(s, 31)


def yellow(s: str) -> str:
    return _colored(s, 33)


def cyan(s: str) -> str:
    return _colored(s, 36)


def green(s: str) -> str:
    return _colored(s, 32)


def _colored(s: str, code: int) -> str:
    return f"\033[{code}m{s}\033[0m"


class TeenyCliError(Exception):
    pass


print = print_

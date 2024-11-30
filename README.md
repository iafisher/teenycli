A tiny library for building CLIs in Python.

Copy [`teenycli.py`](https://github.com/iafisher/teenycli/blob/master/teenycli/teenycli.py) to your `PYTHONPATH` and use it anywhere.

## A brief tour
Command-line argument parsing:

<!-- readme-test: exits -->
```python
from teenycli import ArgP

def main_sub(args):
    print(args.left - args.right)

def main_div(args):
    if args.floor_division:
        print(args.left // args.right)
    else:
        print(args.left / args.right)

argp = ArgP()

argp_sub = argp.subcmd("sub", main_sub)
argp_sub.add("left")
argp_sub.add("--right", required=True)

argp_div = argp.subcmd("div", main_div)
argp_div.add("left")
argp_div.add("right")
argp_div.add("--floor-division")

argp.dispatch()
```

Colors:

```python
from teenycli import red, green, print

print(red("This text is red."))
print(green("This text is green."))
```

Error messages:

```python
from teenycli import warn, error

warn("a warning")
error("an error")
```

Confirmation:

<!-- readme-test: skip -->
```python
from teenycli import confirm

confirmed = confirm("Do you wish to continue?")
```

## Installation
You can install TeenyCLI with `pip install teenycli`. But the main point of TeenyCLI is that it is a single Python file that you can put somewhere on your `PYTHONPATH` and then use in one-off scripts without needing to set up a virtual environment or install anything. Or, you can copy `teenycli.py` into your own project and modify and extend it as you like.

## Why not Click?
[Click](https://click.palletsprojects.com/en/stable/) is a popular library for building command-line applications.

Reasons you might prefer TeenyCLI to Click:

- You don't want to bother with dependency management.
- You want to copy TeenyCLI into your own project as a small and easy-to-understand starting point.
- You prefer an `argparse`-style interface to Click's function decorators.
- You like TeenyCLI's minimal interface and documentation.

Reasons you might prefer Click to TeenyCLI:

- You need Windows support. TeenyCLI has not been tested on Windows. `ArgP` should work, but ANSI colors probably won't.
- You are writing production code and want to depend on a project that is more mature and battle-tested.
- You prefer Click's function decorators to an `argparse`-style interface.
- You need one of the many features that Click supports and TeenyCLI doesn't.

## API reference
### The `ArgP` class

- `ArgP.__init__(version=None, **kwargs)`
  - If `version` is not `None`, then a `--version` flag will be added that prints the version.
  - All other `kwargs` are passed on to `argparse.ArgumentParser`.
- `ArgP.add(*names, *, n = None, required = None, **kwargs) -> ArgP`
  - Add an argument or flag to be parsed.
  - `n` controls how many values will be consumed by the argument. It should be set to one of `ArgP.ZERO`, `ArgP.ONE`, or `ArgP.MANY`. If `None`, it defaults to `ArgP.ZERO` for flags and `ArgP.ONE` for positionals.
  - `required` controls whether the argument must be present.
  - The default value of a `ArgP.MANY` argument is the empty list, not `None` as in `argparse`.
  - All other `kwargs` are passed on to `argparse.ArgumentParser.add_argument`.
  - Returns the same `ArgP` instance so that calls can be chained.
- `ArgP.subcmd(name, handler, *, required=True) -> ArgP`
  - Register a subcommand.
  - `handler` is a function that takes in a single `args` parameter, with the argument values as fields on the object (i.e., `args.my_flag`, not `args["my_flag"]`).
  - Returns a new `ArgP` instance for the subcommand.
  - Nested subcommands are supported.
  - The `required` parameter applies to all subcommands registered on the parent parser, i.e. either the parent parser requires that *some* subcommand be present, or allows there to be no subcommand.
- `ArgP.dispatch(handler=None, *, argv=None)`
  - Parse arguments and dispatch to the handler function.
  - If you registered subcommands with `ArgP.subcmd`, this method will dispatch to the corresponding subcommand handler. Otherwise, you need to pass in your main handler here.
  - `dispatch` returns whatever your handler function returned.
- `ArgP.parse(argv=None)`
  - If you prefer to do dispatch yourself, `parse` will return the parsed arguments without dispatching to a handler.

### User I/O

- `print(message: str, **kwargs) -> None`
  - Wraps built-in `print` to strip ANSI color codes if (a) the output stream is not a terminal, or (b) the `NO_COLOR` environment variable is set to any value.
- `warn(message: str) -> None`:
  - Prints a message to standard error, prefixed by `Warning:` in yellow text.
- `error(message: str) -> None`
  - Prints a message to standard error, prefixed by `Error:` in red text.
- `bail(message: str, *, code = 2) -> NoReturn`
  - Prints an error message, then exits the program.
- `confirm(message: str) -> bool`
  - Prompt the user with `message` and return `True` if they respond "y" or "yes" or `False` if they respond "n" or "no". If the user gives some other response, they will be prompted again until they give a valid response.
- `confirm_or_bail(message: str) -> None`
  - Wraps `confirm` to exit the program if it returns `False`.

### Colors
Colors should be used with `teenycli.print`, which will intelligently strip out colors when appropriate.

- `red(s: str) -> str`
- `yellow(s: str) -> str`
- `cyan(s: str) -> str`
- `green(s: str) -> str`

### Miscellaneous

- `run(cmd, *, shell = False) -> str`
  - Run the command and return standard output as a string.
  - Standard output is decoded to text using the system's default encoding.
  - If the command exits with a non-zero status, `TeenyCliError` is raised.
  - `cmd` is passed on to `subprocess.run`; it can be a list of strings (recommended) or a single string to be parsed by the shell with `shell=True`.

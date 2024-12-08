## [0.1.3] - 2024-12-08
- `ArgP.add` now handles the `default` parameter correctly.

## [0.1.2] - 2024-11-30
- `ArgP` will raise an exception if you try to add both subcommands and positional arguments to the same parser.
- `ArgP.subcmd` now takes a `required` parameter (defaulting to `True`) to allow for optional subcommands.

## [0.1.1] - 2024-11-30
- `ArgP.switch` and `ArgP.arg` methods replaced by single `ArgP.add` method.
- `Args` enum replaced by `ArgP.ZERO`, `ArgP.ONE`, and `ArgP.MANY` constants.
- `ArgP.dispatch` now returns whatever the handler function returned.
- Added `print` function.
- `confirm` now returns a boolean instead of exiting on refusal. The old behavior is available in the new `confirm_or_bail` function.
- `shell` is renamed to `run`. It now takes a `shell` parameter (passed on to `subprocess.run`), and raises a `TeenyCliError` exception instead of `subprocess.CalledProcessError` if the command returns a non-zero status.
- `error`, `warn`, and `bail` automatically strip out ANSI color codes when appropriate.
- The color functions will always return a string with ANSI color codes. The stripping behavior is moved to the `print` function.

## [0.1.0] - 2024-11-29
- Initial release.

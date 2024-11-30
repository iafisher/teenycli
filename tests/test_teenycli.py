import unittest
from pathlib import Path
from typing import List, Tuple

import teenycli
from teenycli import ArgP, TeenyCliError


class TestArgP(unittest.TestCase):
    def test_flags_and_arguments(self):
        argp = ArgP()
        argp.add("--long")
        argp.add("--color", n=ArgP.ONE)
        argp.add("paths", n=ArgP.MANY)

        args = argp.parse(["a", "b", "c"])

        self.assertEqual(["a", "b", "c"], args.paths)
        self.assertEqual(False, args.long)
        self.assertEqual(None, args.color)

        args = argp.parse(["a", "--long", "--color", "auto"])

        self.assertEqual(["a"], args.paths)
        self.assertEqual(True, args.long)
        self.assertEqual("auto", args.color)

        with self.assertRaises(SystemExit):
            argp.parse([])

        with self.assertRaises(SystemExit):
            argp.parse(["--long"])

        with self.assertRaises(SystemExit):
            argp.parse(["a", "--color"])

        with self.assertRaises(SystemExit):
            argp.parse(["a", "--unknown-flag"])

    def test_optional_flag_with_many(self):
        argp = ArgP()
        argp.add("--paths", n=ArgP.MANY)

        args = argp.parse(["--paths", "a", "b", "c"])

        self.assertEqual(["a", "b", "c"], args.paths)

        args = argp.parse([])

        self.assertEqual([], args.paths)

        with self.assertRaises(SystemExit):
            argp.parse("--paths")

    def test_required_flag_with_many(self):
        argp = ArgP()
        argp.add("--paths", n=ArgP.MANY, required=True)

        args = argp.parse(["--paths", "a", "b", "c"])

        self.assertEqual(["a", "b", "c"], args.paths)

        with self.assertRaises(SystemExit):
            args = argp.parse([])

        with self.assertRaises(SystemExit):
            argp.parse("--paths")

    def test_required_flag_with_one(self):
        argp = ArgP()
        argp.add("--output", n=ArgP.ONE, required=True)

        args = argp.parse(["--output", "test.txt"])

        self.assertEqual("test.txt", args.output)

        with self.assertRaises(SystemExit):
            args = argp.parse([])

        with self.assertRaises(SystemExit):
            args = argp.parse(["--output"])

    def test_optional_positional(self):
        argp = ArgP()
        argp.add("maybe", default=None)

        args = argp.parse([])

        self.assertEqual(None, args.maybe)

        args = argp.parse(["yes"])

        self.assertEqual("yes", args.maybe)

        with self.assertRaises(SystemExit):
            argp.parse(["a", "b"])

    def test_dispatch(self):
        main = lambda args: args.x

        argp = ArgP()
        argp.add("-x", required=True, type=int)

        r = argp.dispatch(main, argv=["-x", "42"])

        self.assertEqual(42, r)

    def test_two_subcmds(self):
        main_add = lambda args: args.left + args.right
        main_sub = lambda args: args.left - args.right

        argp = ArgP()
        argp_add = argp.subcmd("add", main_add)
        argp_add.add("left", type=int)
        argp_add.add("right", type=int)
        argp_sub = argp.subcmd("sub", main_sub)
        argp_sub.add("left", type=int)
        argp_sub.add("right", type=int)

        r = argp.dispatch(argv=["sub", "80", "38"])

        self.assertEqual(42, r)

        r = argp.dispatch(argv=["add", "20", "22"])

        self.assertEqual(42, r)

        with self.assertRaises(SystemExit):
            argp.dispatch(argv=[])

    def test_nested_subcmds(self):
        main_outer = lambda _: "outer"
        main_inner = lambda _: "inner"

        argp = ArgP()
        argp_outer = argp.subcmd("outer", main_outer)
        argp_outer.subcmd("inner", main_inner, required=False)

        r = argp.dispatch(argv=["outer", "inner"])

        self.assertEqual("inner", r)

        r = argp.dispatch(argv=["outer"])

        self.assertEqual("outer", r)

        with self.assertRaises(SystemExit):
            argp.dispatch(argv=[])

    def test_very_nested_subcmds(self):
        make_subcmd = lambda name: lambda _: name

        # utils
        #   date
        #     range
        #   math
        #     add
        #     sub
        argp = ArgP()
        argp_utils = argp.subcmd("utils", make_subcmd("utils"))
        argp_date = argp_utils.subcmd("date", make_subcmd("date"))
        argp_date.subcmd("range", make_subcmd("date range"), required=False)
        argp_math = argp_utils.subcmd("math", make_subcmd("math"))
        argp_math.subcmd("add", make_subcmd("math add"))
        argp_math.subcmd("sub", make_subcmd("math sub"))

        r = argp.dispatch(argv=["utils", "date"])

        self.assertEqual("date", r)

        r = argp.dispatch(argv=["utils", "date", "range"])

        self.assertEqual("date range", r)

        r = argp.dispatch(argv=["utils", "math", "add"])

        self.assertEqual("math add", r)

        r = argp.dispatch(argv=["utils", "math", "sub"])

        self.assertEqual("math sub", r)

        with self.assertRaises(SystemExit):
            argp.dispatch(argv=[])

        with self.assertRaises(SystemExit):
            argp.dispatch(argv=["utils"])

        with self.assertRaises(SystemExit):
            argp.dispatch(argv=["utils", "math"])

    def test_mini_git(self):
        make_subcmd = lambda name: lambda args: (name, args)

        argp = ArgP()
        argp.add("-C", required=False, dest="change")
        argp_commit = argp.subcmd("commit", make_subcmd("commit"))
        argp_commit.add("paths", n=ArgP.MANY, required=False)
        argp_commit.add("-m", "--message", required=False)
        argp_add = argp.subcmd("add", make_subcmd("add"))
        argp_add.add("paths", n=ArgP.MANY)
        argp_add.add("-i", dest="interactive")
        argp_checkout = argp.subcmd("checkout", make_subcmd("checkout"))
        argp_checkout.add("branch")
        argp_diff = argp.subcmd("diff", make_subcmd("diff"))
        argp_diff.add("--no-index")
        argp_diff.add("left")
        argp_diff.add("right")

        r = argp.dispatch(
            argv=["-C", ".", "commit", "--message", "Lorem ipsum", "a.txt", "b.txt"]
        )

        self.assertEqual(r[0], "commit")
        self.assertEqual(r[1].change, ".")
        self.assertEqual(r[1].message, "Lorem ipsum")
        self.assertEqual(r[1].paths, ["a.txt", "b.txt"])

        r = argp.dispatch(argv=["add", "-i", "a.txt"])

        self.assertEqual(r[0], "add")
        self.assertEqual(r[1].interactive, True)
        self.assertEqual(r[1].paths, ["a.txt"])

        r = argp.dispatch(argv=["checkout", "master"])

        self.assertEqual(r[0], "checkout")
        self.assertEqual(r[1].branch, "master")

        r = argp.dispatch(argv=["diff", "a.txt", "b.txt"])

        self.assertEqual(r[0], "diff")
        self.assertEqual(r[1].no_index, False)
        self.assertEqual(r[1].left, "a.txt")
        self.assertEqual(r[1].right, "b.txt")

    def test_api_errors(self):
        with self.assertRaisesRegex(
            TeenyCliError, r"`arg=ZERO` and `required=True` are incompatible\."
        ):
            ArgP().add("-x", n=ArgP.ZERO, required=True)

        with self.assertRaisesRegex(
            TeenyCliError, r"`arg=ZERO` is invalid for positional arguments.*"
        ):
            ArgP().add("x", n=ArgP.ZERO)

        with self.assertRaisesRegex(
            TeenyCliError, r"You need to pass at least one name to `add\(\)`\."
        ):
            ArgP().add()

        with self.assertRaisesRegex(
            TeenyCliError, r"`required=True` is incompatible with passing `default`\."
        ):
            ArgP().add("-x", default=0, required=True)

        with self.assertRaisesRegex(
            TeenyCliError, r"The `required` parameter must be specified exactly once"
        ):
            argp = ArgP()
            argp.subcmd("s1", no_op)
            argp.subcmd("s2", no_op, required=False)

        with self.assertRaisesRegex(
            TeenyCliError,
            r"A parser with subcommands cannot also have positional arguments",
        ):
            argp = ArgP()
            argp.subcmd("subcmd", no_op)
            argp.add("positional")

        with self.assertRaisesRegex(
            TeenyCliError,
            r"A parser with subcommands cannot also have positional arguments",
        ):
            argp = ArgP()
            argp.add("positional")
            argp.subcmd("subcmd", no_op)


def no_op(_) -> None:
    return None


class TestMiscellaneous(unittest.TestCase):
    def test_run(self):
        stdout = teenycli.run(["echo", "hello, world!"])
        self.assertEqual("hello, world!\n", stdout)

        with self.assertRaisesRegex(
            TeenyCliError, "Command.*returned non-zero exit status"
        ):
            teenycli.run("false", shell=True)


class TestReadmeCode(unittest.TestCase):
    def test_readme(self):
        readme = (Path(__file__).absolute().parent.parent / "README.md").read_text()
        code_blocks = extract_python_code_from_markdown(readme)
        for code_block, expect_exit in code_blocks:
            if expect_exit:
                with self.assertRaises(SystemExit):
                    exec(code_block)
            else:
                exec(code_block)


def extract_python_code_from_markdown(text: str) -> List[Tuple[str, bool]]:
    in_block = False
    next_block_exits = False
    skip_next_block = False
    r: List[Tuple[List[str], bool]] = []

    for line in text.splitlines():
        stripped = line.strip()
        if in_block:
            if stripped == "```":
                in_block = False
            else:
                r[-1][0].append(line)
        else:
            if stripped == "<!-- readme-test: exits -->":
                next_block_exits = True
            elif stripped == "<!-- readme-test: skip -->":
                skip_next_block = True
            elif stripped == "```python":
                if skip_next_block:
                    skip_next_block = False
                else:
                    in_block = True
                    r.append(([], next_block_exits))
                    next_block_exits = False

    return [("\n".join(lines), expect_exit) for lines, expect_exit in r]

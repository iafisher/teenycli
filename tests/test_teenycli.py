import unittest

from teenycli import ArgP


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

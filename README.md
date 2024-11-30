A tiny library for building CLIs in Python.

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

user_confirmed = confirm("Do you wish to continue?")
```

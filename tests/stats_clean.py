#!/usr/bin/python3

import os
import sys
import argparse
# add search paths seen from project root folder
# (used for vscode test integration)
sys.path.insert(0, "source")
# add search paths when run from inside test folder
# (used when running test directly)
sys.path.insert(0, "../source")
import tools.common

"""
This script cleans test statistics to the last n statistics per test (if available).
If set to zero or if less then n stat entries are available for a test, then the whole
stats file is removed for that test.
"""

parser = argparse.ArgumentParser(description='Clean hBPF testcase statistics')
parser.add_argument("keep", type=int, default=2, nargs="?",
                    help="how many most recent test statistic entries to keep. " +
                    "Set to 0 to delete all (default 2)")
parser.add_argument("-r", "--remove-empty", default=False, action="store_true",
                    help="remove statistic files if they are empty (default False)")
parser.add_argument("-D", "--delete-all", default=False, action="store_true",
                    help="delete all statistic files regardless of other options. " +
                    "(default False)")
args = parser.parse_args()

if args.delete_all:
    args.keep = 0
    args.remove_empty = True

# Gather statistic files per testcase
base_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
result = []
for dirname, dirnames, filenames in os.walk(base_path):
    dirname = (os.path.relpath(dirname, base_path) + "/").replace("./", "")
    for filename in filenames:
        if filename.endswith(".stats") and not filename.startswith("."):
            result.append(os.path.join(base_path, dirname, filename))
result = sorted(result)

# Trim each tests statistic file to n entries or less
tests = []
removed = 0
truncated = 0

for filename in result:

    if args.keep > 0:
        lines = []
        with open(filename, "r+") as tfd:
            lines = tools.common.tail(tfd, args.keep)
            tfd.truncate(0)
            tfd.seek(0)

            if lines:
                print(f"Truncate statistics file: {filename}")
                truncated += 1
                for line in lines:
                    l = line.strip().strip('\x00')
                    tfd.write("{}\n".format(l))
            else:
                if args.remove_empty:
                    print(f"Remove statistics file: {filename}")
                    removed += 1
                    os.remove(filename)
    else:
        print(f"Remove statistics file: {filename}")
        removed += 1
        os.remove(filename)

if args.keep > 0:
    print(f"\n{removed} files removed, {truncated} truncated to {args.keep} entries\n")
else:
    print(f"\n{removed} files removed\n")

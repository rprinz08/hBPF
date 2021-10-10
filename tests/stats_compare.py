#!/usr/bin/python3

import os
import sys
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
# add search paths seen from project root folder
# (used for vscode test integration)
sys.path.insert(0, "source")
# add search paths when run from inside test folder
# (used when running test directly)
sys.path.insert(0, "../source")
import tools.common

"""
This script collects the last statistic information from unit-test statistic
files and creates a single CSV file for further processing. It also creates
a bar chart graphic showing CPU cycles per test.
"""

parser = argparse.ArgumentParser(description="Compare hBPF testcase statistics",
                    epilog="Result numbers can be positive or negative and " +
                    "select lines of test result files. Positive numbers select " +
                    "result lines from the start of test result files " +
                    "(oldest to newest results), negative numbers select lines " +
                    "starting from end of result files (newest to oldest)")
parser.add_argument("-f", "--first", type=int, default=-2, nargs="?",
                    help="First result to use. (default -2, second newest test " +
                    "result)")
parser.add_argument("-s", "--second", type=int, default=-1, nargs="?",
                    help="Second result to use (default -1, newest test result")
parser.add_argument("-t", "--title", type=str, default="", nargs="?",
                    help="Optional graph title")
args = parser.parse_args()
if args.first == 0:
    args.first = -1
if args.second == 0:
    args.second = -2
args.title = args.title.strip()


date = datetime.now().strftime("%Y%m%d-%H%M%S")

# Gather last statistics entry for each test case
base_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
result = []
for dirname, dirnames, filenames in os.walk(base_path):
    dirname = (os.path.relpath(dirname, base_path) + "/").replace("./", "")
    for filename in filenames:
        if filename.endswith(".stats") and not filename.startswith("."):
            result.append(os.path.join(base_path, dirname, filename))
result = sorted(result)

# Combine collected test statistics and write CSV file and graphic
tests = []
cycles1 = []
cycles2 = []
diff = []
diffp = []
for filename in result:
    testname = os.path.splitext(os.path.split(filename)[1])[0]
    lines = []

    with open(filename) as tfd:
        # Select first test result statistics
        if args.first < 0:
            lines = tools.common.tail(tfd, abs(args.first))
            if len(lines) < abs(args.first):
                print(f"{testname}: Want to select statistic result {args.first} "
                    "as first but too few results available")
                continue
            stats1 = lines[0].strip()
        elif args.first > 0:
            lines = tools.common.head(tfd, args.first)
            if len(lines) < args.first:
                print(f"{testname}: Want to select statistic result {args.first} "
                    "as first but too few available")
                continue
            stats1 = lines[len(lines)-1].strip()
        else:
            # 0 = invalid
            print("Select first 0 statistic results - this should not happen")
            sys.exit(1)

        # Select second test result statistics
        if args.second < 0:
            lines = tools.common.tail(tfd, abs(args.second))
            if len(lines) < abs(args.second):
                print(f"{testname}: Want to select statistic result ({args.second}) "
                    "as second but too few available")
                continue
            stats2 = lines[0].strip()
        elif args.second > 0:
            lines = tools.common.head(tfd, args.second)
            if len(lines) < args.second:
                print(f"{testname}: Want to select statistic result ({args.second}) "
                    "as second but too few available")
                continue
            stats2 = lines[len(lines)-1].strip()
        else:
            # 0 = invalid
            print("Select second 0 statistic results - this should not happen")
            sys.exit(1)

    c1 = int(stats1.split(",")[2])
    c2 = int(stats2.split(",")[2])
    diff.append(c1 - c2)
    p = (100 * (c1 - c2)) / c1
    diffp.append(p)

    #print(f"Test: {testname}")
    #print(f"    1: {stats1}")
    #print(f"    2: {stats2}")

    do_graph = int(stats1.split(",")[5])
    if do_graph > 0:
        tests.append(testname)
        cycles1.append(c1)
        cycles2.append(c2)

#print(f"Average cycle reduction: {sum(diff) / len(diff)} cycles, " +
#    f"{sum(diffp) / len(diffp)} %")
print(f"Average cycle reduction: {sum(diffp) / len(diffp)} %")

# Create graph from testcase statistics result where enabled
plt.rcdefaults()
fig, ax = plt.subplots()

y_pos = np.arange(len(tests))

ax.barh(y_pos-0.225, cycles1, height=0.45, align="center", color='b')
ax.barh(y_pos+0.225, cycles2, height=0.45, align="center", color='r')

ax.set_yticks(y_pos)
ax.set_yticklabels(tests)
ax.invert_yaxis()  # labels read top-to-bottom
ax.set_xlabel("CPU Cycles")
#ax.set_title(f"hBPF CPU test comparison\nAverage cycle reduction: "
#    f"{sum(diff) / len(diff):.2f} cycles, {sum(diffp) / len(diffp):.2f} %")
title = f"hBPF CPU test comparison\nAverage cycle reduction: " + \
        f"{sum(diffp) / len(diffp):.2f} %"
if args.title:
    title += f"\n{args.title}"
ax.set_title(title)
ax.autoscale(tight=True)

for i, v in enumerate(cycles1):
    ax.text(3, i - .11, str(v))
for i, v in enumerate(cycles2):
    ax.text(3, i + .36, str(v))
    ax.text(v + 3, i + .36, f"{diff[i]} cyc, {diffp[i]:.2f} %")

plt.subplots_adjust(top=0.983, bottom=0.02, left=0.19, right=0.95)
plt.margins(0.06, 0.001)
fig.set_size_inches(10, 40, forward=True)

#plt.show()
plt.savefig(f"./statistics/test_statistics_compare_{date}.png")

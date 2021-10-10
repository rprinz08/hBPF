#!/usr/bin/python3

import os
import sys
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
cycles = []
with open(f"./statistics/test_statistics_{date}.csv", "w") as fd:
    for filename in result:

        lines = []
        with open(filename) as tfd:
            lines = tools.common.tail(tfd, 1)

        if lines:
            stats = lines[0].strip()

            testname = os.path.splitext(os.path.split(filename)[1])[0]
            fd.write("{},\"{}\"\n".format(stats, testname))

            do_graph = int(stats.split(",")[5])
            if do_graph > 0:
                tests.append(testname)
                c = int(stats.split(",")[2])
                cycles.append(c)

# Create graph from testcase statistics result where enabled
plt.rcdefaults()
fig, ax = plt.subplots()

y_pos = np.arange(len(tests))

ax.barh(y_pos, cycles, align="center")
ax.set_yticks(y_pos)
ax.set_yticklabels(tests)
ax.invert_yaxis()  # labels read top-to-bottom
ax.set_xlabel("CPU Cycles")
ax.set_title("hBPF CPU test performance")

for i, v in enumerate(cycles):
    ax.text(v + 3, i + .25, str(v))

plt.subplots_adjust(top=0.99, bottom=0.02, left=0.19, right=0.95)
plt.margins(0.06, 0.001)
fig.set_size_inches(10, 40, forward=True)

#plt.show()
plt.savefig(f"./statistics/test_statistics_{date}.png")

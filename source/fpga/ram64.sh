#!/bin/bash

S=`basename $0`
Sx="${S%.*}"
#P=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
P="$( dirname "$( readlink -f "$0" )" )"

python3 "./${Sx}.py"
gtkwave "./${Sx}_rw.vcd" "./${Sx}.gtkw" &
gtkwave "./${Sx}_ro.vcd" "./${Sx}.gtkw" &

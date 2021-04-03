#!/bin/bash

S=`basename $0`
P="$( dirname "$( readlink -f "$0" )" )"

export PYTHONPATH="${P}/..:${PYTHON_PATH}"

#SINGLE_STEP=--step
"${P}/main.py" \
	--program "${P}/../../tests/samples/test_pgm_mem.bin" \
	--data "${P}/../../tests/samples/test_data_mem.bin" \
	$SINGLE_STEP


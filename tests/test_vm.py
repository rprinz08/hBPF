#!/usr/bin/env python3

import sys
# add search paths seen from project root folder
# (used for vscode test integration)
sys.path.insert(0, 'source')
sys.path.insert(0, 'tools/ubpf')
# add search paths when run from inside test folder
# (used when running test directly)
sys.path.insert(0, '../source')
sys.path.insert(0, '../tools/ubpf')

import unittest
import colour_runner.runner
import os
import gc
import tempfile
import struct
import random
import re
import ntpath
import ubpf.assembler
import tools.testdata
from emulator.ebpf.vm import *


class TestVM(unittest.TestCase):

    def check_datafile(self, filename):
        """
        Given assembly source code and an expected result, run the eBPF program and
        verify that the result matches.
        """

        td = tools.testdata.read(filename)

        self.assertFalse('asm' not in td and 'raw' not in td,
                    'no asm or raw section in datafile')

        #self.assertFalse('result' not in td and 'error' not in td and 'error pattern' not in td,
        #            'no result or error section in datafile')

        # Prepare program memory
        if 'raw' in td:
            code = b''.join(struct.pack('>Q', x) for x in td['raw'])
        else:
            code = ubpf.assembler.assemble(td['asm'])
            td['raw'] = code

        # Convert byte array to list of uint's in on host byte order
        words = len(code) // 8
        pgm_mem = list(struct.unpack('={}Q'.format(words), code))

        # Dump program memory for debug.
        # print("----- Program memory -----")
        # dbg_pgm_mem = list(struct.unpack('>{}Q'.format(words), code))
        # for i, opc in enumerate(dbg_pgm_mem):
        #    print("%04x: %016x" % (i, opc))

        # Prepare data memory
        data_mem = td.get('mem')
        if isinstance(data_mem, bytes):
            data_mem = list(data_mem)
        else:
            data_mem = None

        # Prepare result to check
        result = None
        if 'result' in td:
            result = int(td['result'], 0)

        expected_error = 0
        expected_error_msg = None
        if 'error' in td:
            expected_error = 1
            expected_error_msg = td['error']

        expected = dict(re.findall(r'(\S+)\s*=\s*(".*?"|\S+)', td.get('expected', '')))
        #print(expected)
        # this can override error section above
        expected_error = 1 if int(expected.get('error', str(expected_error)), 0) > 0 else 0
        expected_error_msg = expected.get('error_msg', str(expected_error_msg))
        disable_test = int(expected.get('disable_emu_test', str("0")))

        if disable_test == 1:
            self.skipTest("Testcase not available for Emulator test")

        # register some helper functions
        def gather_bytes(r1, r2, r3, r4, r5):
            return ((r1 << 32) |
                (r2 << 24) |
                (r3 << 16) |
                (r4 << 8) |
                r5)

        def helper_print(r1, r2, r3, r4, r5):
            pass

        def helper_random(r1, r2, r3, r4, r5):
            return random.randint(0, MAX_UINT64)

        helpers = {
            0: gather_bytes,
            6: helper_print,
            7: helper_random
        }

        # instantiate VM
        print()
        vm = VM(mem=pgm_mem, color=False, debug=False, swap_endian=False,
                call_handler=helpers)
        vm.data_mem = data_mem

        # set r1 - r5 input arguments
        args = td.get("args", {})
        r1 = int(str(args.get("r1", 0)), 0)
        r2 = int(str(args.get("r2", 0)), 0)
        r3 = int(str(args.get("r3", 0)), 0)
        r4 = int(str(args.get("r4", 0)), 0)
        r5 = int(str(args.get("r5", 0)), 0)
        vm.r1 = r1
        vm.r2 = r2
        vm.r3 = r3
        vm.r4 = r4
        vm.r5 = r5

        print("Input:")
        print("R1: ({:20}, 0x{:016x}), R2: ({:20}, 0x{:016x})".format(r1, r1, r2, r2))
        print("R3: ({:20}, 0x{:016x}), R4: ({:20}, 0x{:016x})".format(r3, r3, r4, r4))
        print("R5: ({:20}, 0x{:016x})".format(r5, r5))

        if expected_error:
            with self.assertRaises(Exception) as context:
                vm.start()
            if expected_error_msg is not None:
                self.assertRegex(str(context.exception), expected_error_msg)
        else:
            vm.start()
        r0 = vm.r0

        # Check result
        print("Output:")
        print("R0: ({:20}, 0x{:016x})".format(r0, r0))

        if result is not None:
            self.assertEqual(r0, result,
                ("Received result ({}, 0x{:08x}) not equal expected " +
                "({}, 0x{:08x})").format(
                    r0, r0, result, result))


# Generate a testcase for each test data file when module is loaded.
def generate_testcase(filename):
    def test(self):
        gc.collect()
        self.check_datafile(filename)
        gc.collect()
    return test

base_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
for filename in tools.testdata.list_files(base_path):
    filebase = filename
    if filename.startswith(base_path):
        filebase = filename[len(base_path):]
    testname = 'test_' + '_'.join(os.path.splitext(filebase)[0].split(os.sep)).strip('_')
    setattr(TestVM, testname, generate_testcase(filename))


if __name__ == '__main__':
    # Use colored testrunner instead of standard testrunner.
    #unittest.main()
    runner = colour_runner.runner.ColourTextTestRunner(sys.stdout, verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVM)
    runner.run(suite)

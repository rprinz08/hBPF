import os
import math
import struct


def get_data(filename, data_width_bits=32, endianness="big"):

    assert data_width_bits in [8, 16, 32, 64], \
        "Only 8, 16, 32, 64-Bit data withs supported"

    data_width_bytes = math.ceil(data_width_bits/8)
    data_size = os.stat(filename).st_size
    data = [0]*math.ceil(data_size/data_width_bytes)
    conv = {1: "B", 2: "H", 4: "I", 8: "L"}.get(data_width_bytes, "B")

    print("filename:                {}".format(filename))
    print("file size (bytes):       {}".format(data_size))
    print("data word width (bits):  {}".format(data_width_bits))
    print("data word width (bytes): {}".format(data_width_bytes))
    print("data size (words):       {}".format(len(data)))
    print("conv char:               {}".format(conv))

    with open(filename, "rb") as f:
        i = 0
        while True:
            w = f.read(data_width_bytes)
            if not w:
                break
            if len(w) != data_width_bytes:
                for _ in range(len(w), data_width_bytes):
                    w += b'\x00'
            if endianness == "little":
                data[i] = struct.unpack("<"+conv, w)[0]
            else:
                data[i] = struct.unpack(">"+conv, w)[0]
            i += 1
    return data


def tail(fd, lines=1, buffer=4098):
    """Tail a file and get X lines from the end"""

    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            fd.seek(block_counter * buffer, os.SEEK_END)
        # Either file is too small, or too many lines requested.
        except IOError:
            fd.seek(0)
            lines_found = fd.readlines()
            break

        lines_found = fd.readlines()

        # Decrement the block counter to get the next X bytes.
        block_counter -= 1

    return lines_found[-lines:]

import sys
from os import access, R_OK
from os.path import isfile
from litex import RemoteClient

DEFAULT_WB_HOST = "localhost"
DEFAULT_WB_PORT = 1234
DEFAULT_CSR_FILE = "csr.csv"


def wb_add_std_args(parser):
    parser.add_argument("--host", type=str, default=DEFAULT_WB_HOST, required=False,
                        help=f"Wishbone proxy host, defaults to ({DEFAULT_WB_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_WB_PORT, required=False,
                        help=f"Wishbone proxy port, defaults to ({DEFAULT_WB_PORT})")
    parser.add_argument("--csr", "-c", type=str, default=DEFAULT_CSR_FILE, required=False,
                        help=f"CSR configuration file, defaults to ({DEFAULT_CSR_FILE})")


def wb_open(host, port, csr, debug=False, parser=None):
    try:
        wb = RemoteClient(host=host, port=port, csr_csv=csr, debug=debug)
        wb.open()
    except Exception as ex:
        if not parser is None:
            parser.print_help(sys.stderr)
        print(f"\nError : Unable to connect to Wishbone proxy host ({host}:{port})",
            file=sys.stderr)
        print(f"Reason: {ex}\n",
            file=sys.stderr)
        sys.exit(2)
    return wb


def wb_close(wb):
    try:
        wb.close()
    except:
        pass


def wb_check_file(filepath, parser=None, rtc=1):
    if not (isfile(filepath) and access(filepath, R_OK)):
        if not parser is None:
            parser.print_help(sys.stderr)
        print(f"\nError: File ({filepath}) doesn't exist or isn't readable\n",
            file=sys.stderr)
        sys.exit(rtc)


def wb_dump(bus, from_addr, words_to_dump, bytes_per_word=4, page_reg=None, page_base=0, page_size=512):
    page = 0
    last_page = -1
    ps = page_size * 4
    mask = (2 ** (ps.bit_length() - 1)) - 1

    hex_str = ""
    print(f"Dump {words_to_dump} words ({words_to_dump * bytes_per_word} " +
        f"bytes) @ address (0x{from_addr:04x}), ", end="")
    print(f"page size ({page_size}), * = page change")
    print("addr bus | addr mem |page| data                                            | ascii")
    print("---------------------------------------------------------------------------------------------")

    #for i in range(int(words_to_dump / bytes_per_word)):
    for i in range(words_to_dump):

        bus_addr = from_addr + (4 * i)
        mem_addr = from_addr + i
        if page_reg:
            page = (bus_addr - page_base) // ps

        if i % (16 / bytes_per_word) == 0:
            if hex_str:
                print("{0:08x} | {1:08x} | {2:2d} |{3:49s}| {4}".format(
                    start_addr, start_addr_mem, start_page, hex_str, ascii_str))
            hex_str = " "
            ascii_str = ""
            start_addr = bus_addr
            start_addr_mem = mem_addr
            start_page = page

        if page_reg:
            if page != last_page:
                bus.write(page_reg, page)
                last_page = page
                hex_str = hex_str[:-1] + "*"

        page_addr = page_base + (bus_addr & mask)

        data = bus.read(page_addr)

        for j in range(bytes_per_word):
            shift = (8 * j)
            byte = (data & (0xff << shift)) >> shift
            hex_str = hex_str + "{0:02x}".format(byte)
            ascii_str = ascii_str + ("." if byte < 32 or byte > 127 else chr(byte))
        hex_str += " "

    if len(hex_str) > 1:
        print("{0:08x} | {1:08x} | {2:2d} |{3:49s}| {4}".format(
            start_addr, start_addr_mem, page, (hex_str + (" " * 49))[0:49], ascii_str))


def wb_load(bus, from_addr, data, page_reg=None, page_base=0, page_size=512):
    page = 0
    last_page = -1
    ps = page_size * 4
    mask = (2 ** (ps.bit_length() - 1)) - 1
    data_len = len(data)

    for i in range(data_len):

        bus_addr = from_addr + (4 * i)
        mem_addr = from_addr + i

        if page_reg:
            page = (bus_addr - page_base) // ps
            if page != last_page:
                bus.write(page_reg, page)
                last_page = page

        page_addr = page_base + (bus_addr & mask)
        bus.write(page_addr, data[i])


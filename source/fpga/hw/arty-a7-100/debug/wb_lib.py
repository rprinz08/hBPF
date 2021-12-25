
def dump(bus, from_addr, bytes_to_dump):
    hex_str = ""
    for i in range(bytes_to_dump):
        addr = from_addr + 4 * i

        if i % 16 == 0:
            if hex_str:
                print("{0:08x} : {1:48s}: {2}".format(start_addr, hex_str, ascii_str))
            hex_str = ""
            ascii_str = ""
            start_addr = addr

        data = bus.read(addr)
        byte = data & 0xff

        hex_str = hex_str + "{0:02x} ".format(byte)
        ascii_str = ascii_str + ("." if byte < 32 or byte > 127 else chr(byte))

    if hex_str:
        print("{0:08x} : {1:48s}: {2}".format(
            start_addr, (hex_str + (" " * 48))[0:48], ascii_str))

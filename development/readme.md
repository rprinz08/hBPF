## Development

This directory contains samples how to develop eBPF programs. This can be
done in three ways:

### Filter Expressions

Filter expressions are used in tools like Wireshark/Tshark to specify what
type of packets to capture. They consist of a custom Domain Specific Language
(DSL) which is converted into eBPF assembler.

Example
```
# filter all TCP packets to port 22

tcp port 22
```

### Assembler

The low level way to develop eBPF programs directly using opcodes.

### C

High level development in C using [LLVM compiler](https://llvm.org/)


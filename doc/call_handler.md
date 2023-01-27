# Call Handler Extensions

## Introduction

In eBPF, the `call` op-code is used to call selected subroutines in the Linux Kernel (so called *Helper Functions*).

In hBPF, the `call` opcode can be used to extend the CPU depending on the design.

So for example it can provide a hardware implemented
pseudo random number generator (e.g. [LFSR](https://en.wikipedia.org/wiki/Linear-feedback_shift_register)) or I/O functions e.g. to access LEDs.

The concept is similar to [Custom Function Units (CFU)](https://cfu-playground.readthedocs.io/en/latest/) which allow extending a CPU core (e.g. [RISC-V](https://riscv.org/)) by means of special op-codes.

## Implementation

Such a call-handler extension is implemented by means of a special [Migen](https://m-labs.hk/gateware/migen/) Module.

A call-handler takes hBPF registers R1-R5 as input and returns its result in R0. The argument to the `call` opcode is used to select a function implemented in a call-handler and R1-R5 act as inputs to that function. R1-R5 values are preserved during the call.

There is no way to access other hBPF resources (e.g. memory) then registers R1-R5.

Additional signals `stb`, `ack` and `err` are used to signal start and stop as well as error conditions from and to the hBPF CPU.

The following example call-handler implements two functions. Function `1` adds input registers R1 and R2 while function `2` subtracts R2 from R1.

```python
from migen import *

class CallHandler(Module):

    def __init__(self):
        # Inputs
        self.func = func = Signal(64)
        self.r1 = r1 = Signal(64)
        self.r2 = r2 = Signal(64)
        self.r3 = r3 = Signal(64)
        self.r4 = r4 = Signal(64)
        self.r5 = r5 = Signal(64)
        self.stb = stb = Signal()

        # Outputs
        self.ret = ret = Signal(64)
        self.ack = ack = Signal()
        self.err = err = Signal()

        # # #

        self.sync += [
            ack.eq(0),
            err.eq(0),
            If(stb,
                Case(func, {
                    0: [ ret.eq(r1 + r2) ]
                    1: [ ret.eq(r1 - r2) ]
                    "default": [ err.eq(1) ]
                }),
                ack.eq(1)
            )
        ]
```

## Usage

### Gateware

To use this call-helper, in your designs top module, create an instance and provide it to the hBPF CPU constructor.

```python
...
ch = CallHandler()
self.submodules.cpu = CPU(call_handler=ch)
...
```

In a hBPF program the functions of the call-handler can be called like this:

```asm
# Set input registers
mov r1, 10
mov r2, 3
# Call function 1 (subtract)
call 1
# Result is available in R0 after call op-code returns
```

If selected function is not implemented, the call-handler signals this by setting the `err` signal high. This halts program execution by setting CPUs signals `halt` and `error` high.

### Firmware

To call a distinct call handler from an assembler program
just set the input registers and use the `call` opcode
with the number of the helper function to call as
argument. After the call returns the possible result is
available in register R0.

To call a helper function from C

## Examples

Additional examples can be found have a look at the
documented sample [here](../development/C/call.c).

* Gateware

  * [here](../source/fpga/hw/arty-s7-50/call_handler.py) or [here](../source/fpga/hw/arty-s7-50-nic/call_handler.py).

* C

  * [here](../development/C/call.c)

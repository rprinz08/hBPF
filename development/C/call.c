#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <linux/types.h>

/*
    This sample shows how to use C to write eBPF programs for hBPF.
*/

/*
    For already defined eBPF kernel helpers include 'bpf_helpers.h'. They then
    can be called by their name and will generate the propper 'call xyz' opcode.

    For example, calling 'bpf_get_prandom_u32' will generate a 'call 0x07'
    opcode which returns a pseudo random uint32. Just make sure you have a call
    helper in your gateware which implements the helper number (in this
    case 0x07).

    On Linux (Debian/Ubuntu) this header is available after installing
    'libbpf-dev' package with 'apt install libbpf-dev'.
*/
#include <bpf/bpf_helpers.h>

/*
    For non standard helper functions, a prototype must be defined which will
    generate the wanted call opcode. On Linux have a look at
    '/usr/include/linux/bpf.h' for a list of defined helpers or at the man page
    https://man7.org/linux/man-pages/man7/bpf-helpers.7.html

    At the time of this writing (2023.1) there are about 176 helpers defined.

    So to define lets say helper 'foo' with number 200 which takes one u32 and
    returns one u32 the following lines can be used for GCC or LLVM.
    GCC supports an attribute for this.
    See https://gcc.gnu.org/onlinedocs/gcc/BPF-Function-Attributes.html
*/

// For GCC
//static __u32 (*foo)(__u32) __attribute__((kernel_helper(200)));

static __u32 (*foo)(__u32) = (void *) 200;

/*
    An eBPF/hBPF program consists of only one function (regardless how its
    named, no need to be 'main'). The first encountered function in the source
    becomes the main function. It can receive up to 5 inputs corresponding to
    the eBPF registers R1 - R5 and returns the contents of register R0 (or
    nothing if void).

    Other functions cannot be called as there is no "real" call opcode available.
    The call opcode only calls helper functions provided by the kernel (or, for
    hBPF, helper functions implemented in the gateware by a call helper).
*/
__u32 function(__u32 r1, __u32 r2) {

    __u32 r = r1 + r2 + bpf_get_prandom_u32() + foo(42);

    return r;
}

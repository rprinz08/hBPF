# Zybo-Z7

To test and debug hBPF this folder contains a simple
testbench which instantiates a hBPF CPU, connects
its status signals to some LEDs and switches and
creates a serial Wishbone Bridge and LiteScope
Debugger as shown in the following overview picture.

![test-overview](/doc/images/hbpf-test-overview.png)

The physical connections on the Zybo:

![Zybo Z7](doc/images/zybo-z7.jpg)

Build report for the included bitstream can be found [here](doc/top_utilization_place.rpt).
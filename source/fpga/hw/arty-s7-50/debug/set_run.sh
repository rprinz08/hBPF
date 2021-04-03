#!/bin/bash

. ./wb_lib

echo "current hBPF control reg."
mem hbpf_csr_ctl
echo

echo "hBPF reset"
mem hbpf_csr_ctl 1
echo

echo "new hBPF control reg."
mem hbpf_csr_ctl
echo


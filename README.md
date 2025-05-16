# ptwalk - page table walk for QEMU/KVM

Perform a page table walk for a given virtual address using the CR3 register.
This uses the QEMU/KVM monitor API to get the required register values.
Therefore, this GDB plugin will only use on virtual machines using QEMU/KVM.

## Installation

Run the following command in your GDB session or add it to `~/.gdbinit`:

```
source /path/to/pagetablewalk.py
```

## Usage

```
ptwalk <virtual address>
```

This command reads the CR3 register, calculates the paging indices for the given virtual address,
and walks through the PML4, PDPT, PD, and PT entries. It handles 1GB and 2MB huge pages if encountered.
The final output is the physical address corresponding to the virtual address.
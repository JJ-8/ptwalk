import gdb


# Note: this script has been generated using ChatGPT o3-mini with slight modifications
class PageTableWalk(gdb.Command):
    """Perform a page table walk for a given virtual address using the CR3 register.

    Usage: ptwalk <virtual address>

    This command reads the CR3 register, calculates the paging indices for the given virtual address,
    and walks through the PML4, PDPT, PD, and PT entries. It handles 1GB and 2MB huge pages if encountered.
    The final output is the physical address corresponding to the virtual address.
    """

    def __init__(self):
        super(PageTableWalk, self).__init__("ptwalk", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        # enable physical memory mode
        gdb.execute("maintenance packet Qqemu.PhyMemMode:1")

        self.ptwalk(arg, from_tty)

        # revert physical memory mode
        gdb.execute("maintenance packet Qqemu.PhyMemMode:0")

    def ptwalk(self, arg, from_tty):
        # Split arguments (we expect exactly one argument: the virtual address)
        args = gdb.string_to_argv(arg)
        if len(args) != 1:
            print("Usage: ptwalk <virtual address>")
            return

        try:
            # Allow both hex (0x...) and decimal input.
            vaddr = int(args[0], 0)
        except Exception as e:
            print(
                "Invalid address. Please enter a hexadecimal (0x...) or decimal value."
            )
            return

        # Read the CR3 register via GDB.
        try:
            cr3_val = int(gdb.parse_and_eval("$cr3"))
        except Exception as e:
            print("Error reading CR3 register:", e)
            return

        print("CR3 =", hex(cr3_val))
        print("Virtual Address =", hex(vaddr))

        # Calculate paging indices (each index is 9 bits)
        pml4_index = (vaddr >> 39) & 0x1FF
        pdpt_index = (vaddr >> 30) & 0x1FF
        pd_index = (vaddr >> 21) & 0x1FF
        pt_index = (vaddr >> 12) & 0x1FF
        page_offset = vaddr & 0xFFF

        print("PML4 index =", hex(pml4_index))
        print("PDPT index =", hex(pdpt_index))
        print("PD index   =", hex(pd_index))
        print("PT index   =", hex(pt_index))
        print("Page offset =", hex(page_offset))

        # Entry size for each page table entry is 8 bytes.
        entry_size = 8

        # The GDB inferior is used to read memory.
        inferior = gdb.selected_inferior()

        def read_entry(address):
            """Reads an 8-byte entry from memory at the given physical address."""
            try:
                mem = inferior.read_memory(address, entry_size)
                # Convert the bytes to a little-endian integer.
                entry = int.from_bytes(mem.tobytes(), byteorder="little")
                return entry
            except Exception as e:
                print(f"Failed to read memory at {hex(address)}: {e}")
                return

        # CR3 holds the base of the PML4 table. (Lower 12 bits are typically reserved.)
        pml4_base = cr3_val & 0xFFFFFFFFF000

        # Read PML4 entry.
        pml4_entry_addr = pml4_base + pml4_index * entry_size
        pml4_entry = read_entry(pml4_entry_addr)
        if pml4_entry is None:
            return
        print("PML4 Entry @", hex(pml4_entry_addr), "=", hex(pml4_entry))

        if not (pml4_entry & 0x1):
            print("PML4 entry not present!")
            return

        # Extract PDPT base address from the PML4 entry.
        pdpt_base = pml4_entry & 0xFFFFFFFFF000
        pdpt_entry_addr = pdpt_base + pdpt_index * entry_size
        pdpt_entry = read_entry(pdpt_entry_addr)
        if pdpt_entry is None:
            return
        print("PDPT Entry @", hex(pdpt_entry_addr), "=", hex(pdpt_entry))
        if not (pdpt_entry & 0x1):
            print("PDPT entry not present!")
            return

        # Check for a 1GB huge page (bit 7 set).
        if pdpt_entry & (1 << 7):
            # For 1GB pages, bits 30..? form the base address.
            phys_addr = (pdpt_entry & 0xFFFFFC0000000) + (vaddr & 0x3FFFFFFF)
            print("1GB Page detected.")
            print("Physical Address =", hex(phys_addr))
            return

        # Continue with the Page Directory (PD).
        pd_base = pdpt_entry & 0xFFFFFFFFF000
        pd_entry_addr = pd_base + pd_index * entry_size
        pd_entry = read_entry(pd_entry_addr)
        if pd_entry is None:
            return
        print("PD Entry @", hex(pd_entry_addr), "=", hex(pd_entry))
        if not (pd_entry & 0x1):
            print("PD entry not present!")
            return

        # Check for a 2MB huge page.
        if pd_entry & (1 << 7):
            # For 2MB pages, bits 21..? form the base address.
            phys_addr = (pd_entry & 0xFFFFFFE00000) + (vaddr & 0x1FFFFF)
            print("2MB Page detected.")
            print("Physical Address =", hex(phys_addr))
            return

        # Finally, read the Page Table (PT) entry.
        pt_base = pd_entry & 0xFFFFFFFFF000
        pt_entry_addr = pt_base + pt_index * entry_size
        pt_entry = read_entry(pt_entry_addr)
        if pt_entry is None:
            return
        print("PT Entry @", hex(pt_entry_addr), "=", hex(pt_entry))
        if not (pt_entry & 0x1):
            print("PT entry not present!")
            return

        # Compute the physical address: base of the page plus the offset.
        page_base = pt_entry & 0xFFFFFFFFF000
        phys_addr = page_base + page_offset
        print("Physical Address =", hex(phys_addr))


# Instantiate the command so that it is registered with GDB.
PageTableWalk()
print(
    "PageTableWalk command loaded. Use 'ptwalk <virtual address>' to perform a page table walk."
)

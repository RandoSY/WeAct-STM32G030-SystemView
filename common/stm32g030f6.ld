/* STM32G030F6P6: 32 KiB flash, 8 KiB RAM. GNU ld script. */
ENTRY(Reset_Handler)

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 32K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 8K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);
_stack_size = 0x400;
_stack_limit = _estack - _stack_size;
PROVIDE(__heap_size = 0);

SECTIONS
{
    .isr_vector :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector))
    } > FLASH

    .text :
    {
        . = ALIGN(4);
        *(.text .text.*)
        KEEP(*(.rodata.openocd))
        *(.rodata .rodata.*)
        KEEP(*(.init))
        KEEP(*(.fini))
        . = ALIGN(4);
    } > FLASH

    .ARM.extab : { *(.ARM.extab* .gnu.linkonce.armextab.*) } > FLASH
    .ARM.exidx :
    {
        __exidx_start = .;
        *(.ARM.exidx* .gnu.linkonce.armexidx.*)
        __exidx_end = .;
    } > FLASH

    .preinit_array :
    {
        . = ALIGN(4);
        __preinit_array_start = .;
        KEEP(*(.preinit_array*))
        __preinit_array_end = .;
    } > FLASH
    .init_array :
    {
        . = ALIGN(4);
        __init_array_start = .;
        KEEP(*(SORT(.init_array.*)))
        KEEP(*(.init_array))
        __init_array_end = .;
    } > FLASH
    .fini_array :
    {
        . = ALIGN(4);
        __fini_array_start = .;
        KEEP(*(SORT(.fini_array.*)))
        KEEP(*(.fini_array))
        __fini_array_end = .;
    } > FLASH

    _sidata = LOADADDR(.data);
    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data .data.*)
        . = ALIGN(4);
        _edata = .;
    } > RAM AT > FLASH

    .bss (NOLOAD) :
    {
        . = ALIGN(4);
        _sbss = .;
        *(.bss .bss.*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    } > RAM

    .heap_reserve (NOLOAD) :
    {
        . = ALIGN(8);
        _heap_start = .;
        . += __heap_size;
        . = ALIGN(8);
        _heap_end = .;
    } > RAM

    .stack_reserve (NOLOAD) :
    {
        . = ALIGN(8);
        _end = .;
        end = .;
        . += _stack_size;
        _reserved_end = .;
    } > RAM

    /DISCARD/ : { *(.note.GNU-stack) }
}

ASSERT(ADDR(.isr_vector) == ORIGIN(FLASH), "Vector table must start at flash origin")
ASSERT(SIZEOF(.isr_vector) == 184, "STM32G030 vector table must match ST's 46-entry startup table")
ASSERT(_end + _stack_size <= _estack, "RAM does not have room for the 1 KiB stack")

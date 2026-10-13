# Validation scope

GitHub includes the portable JSON summaries below. Raw *.log files and local
VS Code tool settings are excluded from version control; the logs cited below
are retained in the original local project. Reproduce the checks from the
project README after configuring host tools for your computer.

Both images (blink and systemview_demo) pass debug and release builds with Arm
GNU Toolchain 15.2.Rel1. debug_images.json and release_images.json record sizes,
vector checks and image hashes. Both profiles fit 32 KiB flash and 8 KiB RAM.
The trace image reserves 6968 bytes including its 4096-byte RTOS heap,
1024-byte event buffer and 1024-byte main/interrupt stack.

standalone_check.json and relocation.log record relocated builds of both images
in both profiles, with source/include/output paths confined to the copied
package. No original Nucleo folder is a firmware input.

The compiled ARM functions passed 20 timestamp tests (10 in each profile),
covering pre-wrap, pending wrap, wrap between the counter and flag reads,
32-bit rollover, interrupt service and preservation of PRIMASK. Two more tests
executed real V9 task-allocation code: LED, Work and modeled Idle allocations
left 1496 heap bytes. See timestamp_arm_tests.json. This is CPU emulation with
mock timer registers, not a physical timer, scheduler run or measured stack
high-water result. Optional test dependency: unicorn 2.1.4, outside firmware.

All three OpenOCD configurations parsed offline with initialization disabled;
no probe was accessed. Seven VS Code profiles passed installed Cortex-Debug
1.12.1 required-field/enum checks. No VS Code UI session on G030 was exercised.

Hardware is not here yet. These remain pending: target supply and LED polarity,
64 MHz clock/timer rate, sustained rollover continuity, actual task/interrupt
stack margins with recording active, Pico CMSIS-DAP/RTT ownership and live
SystemView capture without lost events. No existing board was flashed.

Board facts were checked against WeAct v1.0 schematic at repository commit
f692e4e2e853ae9610aa337e2222c6d6d73416d8 and ST G030 datasheet DS12991 Rev 6.
The board LED wiring is active-low PA4; PA14/A14 button shares SWCLK.

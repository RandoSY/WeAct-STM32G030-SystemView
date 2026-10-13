# WeAct G030 hardware results — 2026-10-13

Built and flashed the Duke-derived systemview_demo release image through the
user's RP2040/yapicoprobe CMSIS-DAPv2 at 1 MHz SWD, reset_config none.
OpenOCD identified STM32G03x/G04xx rev Z, device ID 0x10016466, 32 KiB flash.
The flash-size identification does not distinguish every G03x part; the
user identifies the populated board as STM32G030F6P6.

A complete 32768-byte original application backup was saved outside the repo
before flashing. OpenOCD programming verification passed, and an 11000-byte
readback matched the built binary byte-for-byte. The board was left running.

OpenOCD/GDB identified LEDtask, WorkTask and IDLE. Two samples showed advancing
LED/work counters and RTOS ticks. SystemCoreClock reported 64000000;
boardFailure, rtosFailure and assertLine were zero. Trace/timestamp readiness
flags were one. This is not an external oscillator-frequency measurement.

Observed memory margins before active SystemView recording:
- Linker reserved RAM: 6968/8192 bytes; 1224 bytes outside reservations.
- FreeRTOS heap remaining: 1496 bytes.
- LED stack minimum unused observed: 148 words / 592 bytes (allocated 192 words).
- Work stack minimum unused observed: 210 words / 840 bytes (allocated 256 words).
- Idle stack minimum unused observed: 106 words / 424 bytes (allocated 128 words).
Task stack figures are high-water observations from this short run, not
worst-case proof. Interrupt/MSP stack high-water was not measured.

OpenOCD live RTT console check passed. Channel 0 was "Terminal", 128 bytes;
channel 1 was "SysView", 1024 bytes. Repeated WorkTask status text was read
from channel 0 via a temporary local TCP server. The server and OpenOCD were
shut down afterward so the user can use VS Code with the probe.

Still pending: a live SystemView timeline, sustained capture/drop checks,
stack margins during active tracing, external timing validation and visual
verification of the new VS Code RTT terminal. No physical UART was enabled.

JSON evidence: hardware_flash.json, hardware_runtime.json,
hardware_rtt_console.json. The raw logs and flash backup remain local.

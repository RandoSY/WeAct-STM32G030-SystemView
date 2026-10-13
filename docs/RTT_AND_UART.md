# Listening to the FreeRTOS demo: RTT and UART

This is project track 1: the Duke-derived STM32G030 FreeRTOS/SystemView demo.
The separate hardware-test Blinky and PX-fwlib port were not modified.

## RTT: no COM port or extra signal wires

The firmware writes into RAM ring buffers described by _SEGGER_RTT. OpenOCD
reads those buffers through the existing Pico/yapicoprobe SWD link while the
CPU runs. Cortex-Debug can display the text in a VS Code terminal.

STM32 RAM -> SWD -> Pico USB -> OpenOCD -> VS Code RTT terminal

Channel 0: text console, 128-byte output buffer.
Channel 1: binary SystemView events, 1024-byte output buffer.
Our console is nonblocking: full/unread output can be dropped so tasks keep
running. The reader must drain the event channel promptly for trace capture.

The board's live RTT channel 0 was tested via OpenOCD and TCP localhost:19021.
Repeated "WorkTask: burst complete" messages were received. That temporary
server was stopped afterward; 19021 is not a permanently running service.
The VS Code RTT configuration was added and schema-checked. After the startup
fix, the user confirmed repeated WorkTask messages in the VS Code RTT terminal. Live SystemView recording is
still pending.

## Read it in VS Code

1. Open this weact_g030_systemview folder, not the hardware-test Blinky folder.
2. In Run and Debug choose "CMSIS-DAP: attach matching release trace image".
   It uses the matching release ELF and does not rebuild or reflash.
3. Press F5. If execution pauses, press Continue/F5.
4. Open the Terminal panel and select the RTT terminal labeled
   "FreeRTOS RTT console". Expect "WorkTask: burst complete" every 500 ms.
5. End the session with Shift+F5 before using another probe-owning tool.

The launch configuration locates _SEGGER_RTT from the matching ELF symbols
and uses the explicit "SEGGER RTT" identifier; its channel-0 console decoder
is enabled. Trace launch/attach runs the firmware for 200 ms and halts before
RTT setup so the RAM control block exists. It pauses after initialization
rather than at main. Press Continue/F5 to receive ongoing output. Both normal trace launch profiles
and the attach profile have this setting. No COM port or baud rate is selected
for this OpenOCD RTT connection. Keep the ELF matched to the flashed image.

## Optional physical UART through yapicoprobe

For a standard RP2040 Pico:
- Pico GP4 (physical pin 6, transmit) -> WeAct PA12 (USART1 receive).
- Pico GP5 (physical pin 7, receive) <- WeAct PA11 (USART1 transmit).
- GND -> GND; use 3.3 V logic.

The STM32 firmware must enable the PA11/PA12 remap and configure USART1.
The current FreeRTOS demo does not initialize UART or output text on those
pins. A suitable initial UART format is 115200 baud, 8 data bits, no parity,
one stop bit. Windows currently identifies COM13 as YAPicoprobe CDC-UART and
COM14 as YAPicoprobe CDC-DEBUG. COM numbers may change on another USB port/PC.
The debug console port belongs to the probe, not the STM32's physical UART.

References:
- https://github.com/Marus/cortex-debug/wiki/SEGGER-RTT-support
- https://www.segger.com/products/debug-probes/j-link/technology/about-real-time-transfer/
- https://github.com/rgrr/yapicoprobe/blob/master/doc/hardware.adoc

## RTT startup error fixed on 2026-10-13

The user reported "Protocol error with Rcmd: 01" on "monitor rtt start".
The CPU was paused at main and the RTT control block was still zero. This
OpenOCD version returns an error when the control block is absent. An explicit
search identifier was also missing from our manually addressed configuration.

The profiles now use a symbol-derived RTT address, explicit SEGGER RTT ID,
and firmware initialization before RTT startup. The same VS Code-owned
OpenOCD server passed rtt start and reported both channels after initialization.
The user subsequently confirmed a successful VS Code session and repeated
WorkTask messages in its RTT terminal.
End the old session with Shift+F5, select the matching-release attach profile,
press F5, and press F5 again to continue.

# Restart context

Standalone WeAct STM32G030F6P6 package: 32 KiB flash, 8 KiB RAM, 64 MHz HSI/PLL.
Two images: blink and systemview_demo. Native FreeRTOS V9, LEDtask and WorkTask;
Pico/yapicoprobe CMSIS-DAP for debug, RTT channel 1 via TCP 19111 for SystemView.
Channel 0 provides a small nonblocking RTT console, without UART wiring.
WeAct active-low LED PA4. GP2 -> CLK/PA14, GP3 -> DIO/PA13, common ground;
optional GP6 -> NRST. A14 button shares SWCLK: leave it alone while probing.

All source dependencies are inside this folder; host tools are external.
Open this folder in VS Code. Build: python build.py all; release adds
--profile release. See README.md for wiring, first blink and live capture.

Debug/release and relocation checks pass. Trace reserves 6968/8192 RAM bytes;
22 compiled ARM emulation tests pass, including timestamp races and modeled
three-task allocation. Modeled heap free: 1496 bytes. This is not hardware proof.

User confirms WeAct and Pico hardware has not arrived. No physical G030 flash,
scheduler/stack/timestamp test or live trace was performed. First hardware stage
is blink, then task/clock checks, then active recording and overflow checks.
The Nucleo F031 and old G031 packages remain separate. Ultimate goal is
SystemView mastery for a user familiar with VS Code/C but not an embedded expert.

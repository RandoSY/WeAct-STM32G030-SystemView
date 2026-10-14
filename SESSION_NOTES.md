# Current result: live SystemView verified (finalized 2026-10-14)

Work remains in track 1, Duke-derived weact_g030_systemview. Keep the user's
hardware-test Blinky and PX-fwlib port separate. Read docs/SYSTEMVIEW_PROGRESS.md
and the updated four-page PDF before following older notes below.

User confirmed the live timeline and supplied a screenshot: 149406 events at
36.902981 s. Saved baseline captures/2026-10-13/WeAct_G030_RTT_195317.SVDat
was genuinely decoded by SystemView: 20273 events, 5.004982 s, zero reported
overflow/loss entries, monotonic timestamps, named tasks and markers.

Run the matching release debug/attach profile, continue, then Tasks: Run Task
> SystemView: start channel 1 bridge. It discovers this project's existing
OpenOCD and bridges raw RTT TCP 19022 to IP recorder 127.0.0.1:19111 with the
required 32-byte hello. Run SystemView: open application and use its Target
menus. Polling is 5 ms; channel 0 stays in the RTT text terminal. The bridge
never builds/flashes or starts a second probe server. A bridge from the agent
terminal may still be running: check/reuse it before launching another.

Active trace: heap free1496 bytes; unused LED/Work/Idle stack140/202/106 words.
Both failure flags zero. MSP high-water and long stress tests not measured.
GUI helper import failed; CLI decoding and user-supplied screenshot established
success. Use SystemView menus to save future recordings; automatic CLI save
around dialogs was unreliable. Earlier pending-live-capture statements are
superseded by this result. See validation/systemview_capture_analysis.json.

## Earlier session history (superseded where marked pending)

# Restart context

This is track 1: Duke STM32F0-to-G0 tutorial/FreeRTOS/SystemView project.
Track 2 is the separate WeAct_G030F6P6_Blinky_Debug_v1.1.4 hardware test.
Track 3 is RandoSY/px-fwlib branch feature/stm32g030-weact-cli. Keep the three
code histories and build outputs separate; reuse proven SWD settings as useful.

On 2026-10-13 the user authorized building/flashing our FreeRTOS demo. The
WeAct/Pico is now available. Release image flashed via CMSIS-DAPv2/OpenOCD,
verify + byte-for-byte readback passed. Original full flash backup is in the
parent output/hardware-backups folder (local only). The board was left running
FreeRTOS; temporary OpenOCD was shut down to release the probe for VS Code.

See validation/HARDWARE_RESULTS.md and hardware_*.json for measured evidence.
Three tasks seen, counters advance, failure flags zero, clock variable 64 MHz.
Heap free 1496 bytes; stack unused minima LED 148/Work 210/Idle 106 words.
RAM reserved 6968/8192; release flash 11000/32768. These margins are from a short
run before active SystemView recording. MSP stack was not measured.

Live RTT channel 0 text passed through OpenOCD/TCP. Channel 1 SysView is present
but live SystemView recording is pending. VS Code trace launch and attach
profiles now enable the channel-0 RTT terminal. The config was schema-checked,
not visually tested in the VS Code GUI. docs/RTT_AND_UART.md explains listening.

No UART is enabled in the demo. Optional standard Pico UART wiring: GP4 TX to
WeAct PA12 RX, GP5 RX to PA11 TX, common GND. Firmware needs pin remap + USART1.
COM13 currently CDC-UART; COM14 CDC-DEBUG. UART wires are unnecessary for RTT.

Build: python build.py systemview_demo --profile release. Debug uses --profile
debug. For the currently flashed image select the matching release attach
profile. Ultimate goal remains live SystemView mastery. Do not overwrite the
separate hardware-test Blinky or PX-fwlib source during track-1 work.

VS Code RTT startup correction: user saw Rcmd 01 while stopped at main, before
RTT initialization. Profiles now use address auto, searchId SEGGER RTT and
post-launch/attach monitor resume; sleep 200; halt; maintenance flush register-cache before RTT setup.
Trace launch pauses after initialization (runToEntryPoint main removed only
for trace profiles). Same VS Code server tested: RTT start PASS, both channels
present. User subsequently confirmed the VS Code RTT terminal displays repeated WorkTask messages. See rtt_startup_fix.json.

The user confirmed live VS Code RTT console text on 2026-10-13. Console channel
0 is working; live SystemView binary channel-1 recording remains the next step.

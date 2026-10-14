# SystemView progress: verified live on the WeAct

Hardware work: 2026-10-13. Documentation finalized: 2026-10-14.
Project track 1 is the Duke-derived weact_g030_systemview. The separate
hardware-test Blinky and earlier PX-fwlib port were not modified.

## Verified result

The user confirmed live activity and supplied a screenshot showing
WeAct G030 Demo [FreeRTOS] on Cortex-M0+, 149,406 events and 36.902981 seconds.
VS Code simultaneously showed the three tasks and repeated RTT console text.

A separate five-second target stream was saved and decoded/exported by the
installed SystemView V4.10b application: 20,273 events over 5.004982 seconds,
both task and marker names, monotonic timestamps, zero reported overflow/lost
events. This is actual hardware data. The clip does not certify arbitrary
long recordings or host load. See validation/systemview_capture_analysis.json.

## Reproduce the working setup

1. Open this folder in VS Code. Attach with the matching release profile,
   or use the release launch profile to rebuild/flash. Continue with F5.
2. Confirm channel-0 text in the FreeRTOS RTT console terminal.
3. Run task SystemView: start channel 1 bridge and leave it running.
4. Run task SystemView: open application. Select IP recorder at
   127.0.0.1, port 19111. Use the Target menu to start/stop recording.
5. Save .SVDat with the matching firmware. The four-page PDF gives UI steps.

Pipeline: STM32 RAM -> SWD -> Pico USB -> VS Code's existing OpenOCD ->
raw RTT channel 1 on TCP 19022 -> systemview_bridge.py -> SystemView IP 19111.
The standard-library Python helper supplies the required 32-byte IP hello,
then forwards commands/events. It never builds, flashes or starts another
probe-owning server. No UART wires, COM port or STM32 network stack are needed.
Polling is 5 ms; channel 0 remains the text console.

## Fixes and measured evidence

RTT startup initially failed at main before its RAM buffers existed. Trace
profiles now initialize firmware for 200 ms, halt, flush the register cache,
and use an explicit SEGGER RTT ID with an ELF-derived address. A raw TCP RTT
socket lacked the IP handshake; the bridge supplies it. The Windows UI SDK
had a missing tslib import, so CLI decoding and user GUI confirmation were
used. CLI stop/save around dialogs was unreliable; use the application menus
to save future live recordings. The saved baseline is an equivalent raw
hardware stream genuinely decoded by SystemView.

| Measurement | Five-second baseline |
|---|---|
| LED period | Median 200 ms; 197.821-202.179 ms range |
| Work period | 499.992-500.008 ms |
| Work burst | 2.007 ms for all 10 observed bursts |
| Idle share | 96.89% |
| Active-trace heap free | 1,496 bytes |
| Unused LED / Work / Idle stack | 140 / 202 / 106 words (560 / 808 / 424 bytes) |
| Board and RTOS failure flags | Zero |

The LED variation is consistent with higher-priority WorkTask preemption.
Stack values are observed minima, not worst-case bounds. MSP stack high-water,
external clock calibration and multi-hour stress captures remain unmeasured.

## Saved artifacts

- docs/WeAct_G030_Pico_SystemView_Quickstart.pdf: updated four-page guide,
  rendered and visually checked on all pages.
- captures/2026-10-13/WeAct_G030_RTT_195317.SVDat: 56,085 target event bytes.
- Matching _contexts.csv and _events.csv.gz: genuine SystemView exports.
- validation/systemview_capture_analysis.json: counts, timing and hashes.
- validation/systemview_active_memory.json: reads without halting the target.
- tests/test_systemview_bridge.py: three real-socket protocol tests passed.
- Matching release ELF and uncompressed event export are preserved locally.

References: https://doc.segger.com/UM08027_SystemView.html and
https://github.com/rgrr/yapicoprobe/blob/master/src/net/net_sysview.c

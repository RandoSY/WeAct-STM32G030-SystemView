# WeAct STM32G030F6P6: a friendly FreeRTOS / SystemView example

Start with the [four-page illustrated quick start](docs/WeAct_G030_Pico_SystemView_Quickstart.pdf).

Open **this folder** in VS Code. This targets the WeAct core board v1.0 with
**STM32G030F6P6**, 32 KiB flash, 8 KiB RAM and an active-low blue LED on **PA4**.
The internal oscillator supplies 64 MHz; the board crystal is not required.
All firmware libraries, startup, linker script and SVD are bundled here.
The Nucleo F031 and previous G031 packages are separate and preserved.

**First hardware checks passed on 2026-10-13.** The release FreeRTOS demo was
flashed and verified on your WeAct board through Pico/yapicoprobe. GDB saw all
three tasks, advancing counters, clear failure flags and 1,496 bytes free in
the RTOS heap. The user confirmed RTT console and live SystemView activity.
A saved clip decoded to 20,273 events with zero reported overflow events.
See [live progress and restart steps](docs/SYSTEMVIEW_PROGRESS.md),
[hardware results](validation/HARDWARE_RESULTS.md) and
[RTT/UART listening instructions](docs/RTT_AND_UART.md).

This is the Duke-derived tutorial project. Your proven hardware-test Blinky
and the earlier PX-fwlib port remain separate projects. Do not flash this
image onto the NUCLEO-F031K6.

## What you will see

There are two images, so each stage has a simple success check:

| Image | Expected behavior |
|---|---|
| `blink` | Blue PA4 LED toggles every 200 ms; checks board power, SWD and clock. |
| `systemview_demo` | LEDtask every 200 ms; WorkTask at higher priority every 500 ms, with an approximately 2 ms elapsed-time work burst; idle between work. |

The demo uses FreeRTOS V9 native task calls. `vTaskDelayUntil` provides a fixed
periodic schedule instead of adding a relative delay after every loop body.
Marker 1 is **LED toggle**; marker 2 is **Work burst**. SysTick schedules RTOS
tasks, TIM17 supplies HAL's tick, and TIM3 supplies trace timestamps.

It runs even when SystemView is closed. The recorder starts/stops tracing over
RTT channel 1. A small nonblocking RTT console on channel 0 writes startup and
work status through yapicoprobe's target/RTT serial interface; no UART wires or
printf heap are required. Console text is dropped when no consumer reads it.

## Build first

For a fresh GitHub clone, first generate this computer's tool paths:

```powershell
python configure_vscode.py --force
```

Machine-specific `.vscode/settings.json` stays local. Launch profiles, build
tasks and extension recommendations are shared. If using a separate Arm GDB,
pass `--gdb "C:/path/to/arm-none-eabi-gdb.exe"` when configuring. Explicit
options also include `--toolchain-bin`, `--openocd` and `--openocd-scripts`.

Host tools: Python 3.9+, Arm GNU Toolchain, Arm GDB, OpenOCD, VS Code with
Cortex-Debug/C/C++, and separately installed SEGGER SystemView. Firmware builds
use Python's standard library, need no pip packages, and need no network.

In VS Code choose File > Open Folder > **the project folder** (locally named
`weact_g030_systemview`; a GitHub clone may have the repository name), then
Terminal > New Terminal:

```powershell
python build.py all
python build.py all --profile release
python check_package.py
```

These produce `build/debug/<image>/firmware.elf` and the corresponding
BIN/HEX/MAP files, with the same layout under `build/release`. Building does
not connect to or flash any hardware. Ctrl+Shift+B builds all debug images.
Both profiles retain debug symbols; debug uses -Og, release uses -Os.

GCC can be found on PATH, via `ARM_GCC_BIN`, or with `--toolchain-bin`.
`python build.py all --verify-only` rechecks existing debug images.

## Pico/yapicoprobe wiring

Install the upstream **yapicoprobe UF2 for your exact Pico board** using its
BOOTSEL procedure. Probe firmware is separate from the STM32 demo. These are
the standard Raspberry Pi Pico firmware assignments; other RP2040 boards can
use different pins.

| Pico pin | WeAct label | Purpose |
|---|---|---|
| GP2 | CLK | PA14 / SWCLK |
| GP3 | DIO | PA13 / SWDIO |
| GND | GND | Common ground |
| GP6, optional | NRST | Target reset |

WeAct P1 schematic pin numbering is **1 = 3V3, 2 = DIO, 3 = CLK, 4 = GND**.
Use the silk labels rather than guessing orientation from a photograph.
There is no onboard debugger sharing these signals. PA13/PA14 remain in their
SWD configuration. **Do not press the A14 button during debugging or tracing:**
it shares PA14/SWCLK. The **NRST** button is the reset button to use.

For a standard Pico and this small standalone board, a convenient single-power
arrangement is Pico **3V3(OUT)** to WeAct **3V3**, with common GND and no second
target power source. Confirm the Pico supply can power your connected circuit
and that it is 3.3 V. Alternatively power WeAct from a suitable supply through
its documented 5V/regulator input and omit the Pico 3V3 wire. Do not connect
two driven 3V3 supplies together or feed 5V into 3V3. Keep SWD wires short.

Reference: [WeAct schematic](https://github.com/WeActStudio/WeActStudio.STM32G0xxC0xxCoreBoard/blob/master/Hardware/WeAct-STM32G0xxC0xxCoreBoard_V10%20SchDoc.pdf),
[Pico probe wiring](https://github.com/rgrr/yapicoprobe/blob/master/doc/hardware.adoc).

## First hardware check: blink

1. Plug the Pico into USB with WeAct wired and powered.
2. In VS Code install the recommended workspace extensions.
3. Open Run and Debug with Ctrl+Shift+D.
4. Select **Pico/yapicoprobe: first blink** and press F5.
5. The image builds, downloads and stops at `main`. Press F5 again.
6. Confirm the blue LED toggles. Pause and check `SystemCoreClock = 64000000`
   and `boardFailure = 0` after initialization. Stop with Shift+F5.

Use a working blink as the gate before trying trace. If OpenOCD cannot connect,
check power, shared ground, CLK/DIO wiring, the probe firmware and exclusive
probe access. The generic OpenOCD G0 target validates the Cortex-M0+ SWD ID;
the flash driver checks device identity. A wrong target is not a porting test.

External ST-Link profiles are supplied as optional fallbacks. They mean a
separate probe wired to this WeAct board, not the Nucleo's onboard target.
The legacy HLA fallback needs an OpenOCD build that still provides that driver.

## Flash and inspect the trace demo

Select **Pico/yapicoprobe: SystemView demo (release)**, press F5, then F5 again
after the initialization pause. Trace profiles initialize RTT before pausing;
they no longer stop at `main`. Run for several seconds, then pause and watch:

```text
SystemCoreClock
uwTick
boardFailure
rtosFailure
ledIterations
workIterations
ledStackWordsFree
workStackWordsFree
idleStackWordsFree
rtosHeapBytesFree
timestampHigh
```

`boardFailure` and `rtosFailure` should be zero. Stack counters are unused
32-bit **words**, so multiply by four for bytes. Zero before a task first runs
is not a measurement. `rtosFailure` 1 means allocation failure, 2 stack overflow,
3 an assertion; `assertLine` and `rtosFailedTask` help locate a stopped failure.
Iteration counts should advance while running. HAL `uwTick` is milliseconds.

OpenOCD RTOS awareness supplies **LEDtask, WorkTask and IDLE** to Call Stack.
Use `info threads` in the Cortex-Debug Debug Console as a fallback while paused.
The matching-release attach profile has no build/download task. Do not attach
with a different ELF. Debugger pauses change timing; capture a run without them.

## Record in SystemView

The verified route shares the existing VS Code OpenOCD session. Keep the MCU
running and use Ctrl+Shift+P > Tasks: Run Task:

1. **SystemView: start channel 1 bridge**. Leave its task terminal running;
   if a bridge is already running, reuse it.
2. **SystemView: open application**. In SystemView choose Target > Recorder
   Configuration > **IP recorder**, IP **127.0.0.1**, port **19111**.
3. Target > Start Recording; record 5-10 seconds; Target > Stop Recording.
4. Close any information dialog with OK, inspect the timeline, and use
   File > Save Recording to preserve the .SVDat with its matching firmware.

`systemview_bridge.py` supplies the 32-byte IP handshake and forwards the raw
OpenOCD channel-1 stream on port 19022. It uses only Python's standard library,
discovers this project's OpenOCD TCL port on Windows, and never starts another
debug server. Other hosts can pass `--tcl-port <port>`. Polling is 5 ms. No COM
port, extra UART wiring or STM32 Ethernet is required. Channel 0 stays in the
FreeRTOS RTT console terminal. The saved baseline is under captures/2026-10-13.

The [updated PDF](docs/WeAct_G030_Pico_SystemView_Quickstart.pdf) documents this
tested workflow, measurements, troubleshooting and saved evidence.

## Optional Pico USB-network route (not the tested setup)

The following earlier procedure uses the Pico's own network recorder instead
of the verified local bridge. Do not mix its address with the workflow above.

1. Finish debugging with Shift+F5 and close that OpenOCD process. Reset WeAct
   with **NRST** so the flashed trace image runs. Only one of yapicoprobe's
   CMSIS-DAP, drag/drop flash service and automatic RTT service can own SWD.
2. Follow yapicoprobe's Windows USB-network setup. Its documented defaults are
   probe **192.168.14.1**, host **192.168.14.2**, TCP port **19111**. Use the
   actual values if your probe was configured differently.
3. Probe RTT discovery should cover **0x20000000 to 0x20002000**, end exclusive.
   For generic targets, yapicoprobe exposes `ram_start` / `ram_end` settings;
   narrow its search to this range if discovery needs help. Follow the exact
   command syntax and restart requirements for your installed probe firmware.
4. Open SystemView. Target > Recorder Configuration > **IP recorder**:
   enter the probe address and port 19111. This is a Pico service; the STM32
   does not need an Ethernet stack or an IP address.
5. Target > Start Recording. Record a few seconds, then Target > Stop Recording.
   Look for **WeAct G030 Demo**, 64 MHz CPU and 1 MHz timestamps, the two
   application task names, and the **LED toggle / Work burst** markers.
6. Save the `.SVDat` and its matching ELF/source/configuration. Record any
   overflow indication before trusting timing measurements.

F5 in VS Code controls debugging; F5 in SystemView starts recording. Use menus
for the first capture to avoid confusing the active window. Onboard ST-Link
debugging of another board does not supply this IP stream.

The firmware waits for the recorder command before collecting events. A short
capture does not fix bursts that overflow the 1 KiB target buffer. Adjust probe
throughput or unnecessary event traffic before changing buffer sizes.

Sources: [yapicoprobe RTT/network/configuration](https://github.com/rgrr/yapicoprobe),
[SystemView recorder instructions](https://doc.segger.com/UM08027_SystemView.html).

## First experiments

Edit **projects/systemview_demo/Inc/demo.h**:

- Change `DEMO_LED_PERIOD_MS` from 200 to 100; expect the LED/task period to halve.
- Change `DEMO_WORK_BURST_US` from 2000 to 4000; expect the Work burst marker to
  become longer and WorkTask to consume more CPU time.
- WorkTask has priority 2 and LEDtask priority 1. Where both wake together,
  expect WorkTask to run first and LEDtask to wait. Look for that delay.

Rebuild, reflash and make a new recording after each change. Use one change at
a time. Keep work bursts shorter than the 500 ms work period. Their configured
length is elapsed time, including interrupt preemption, not pure CPU time.
The SystemView metadata table holds two application tasks; adding more tasks
also requires increasing its capacity and revisiting memory/stack budgets.

## The memory budget

Both final profiles reserve **6,968 / 8,192 RAM bytes**, leaving **1,224 bytes**
outside the reservations. The budget already includes:

| Reservation | Bytes |
|---|---:|
| FreeRTOS heap, containing all task stacks and TCBs | 4,096 |
| SystemView RTT channel 1 event buffer | 1,024 |
| Main/interrupt stack | 1,024 |
| RTT channel 0 console buffer | 128 |
| Remaining globals, RTT metadata, small receive buffers, alignment | 696 |

LED stack is 192 words (768 bytes), Work stack 256 words (1,024 bytes), and
idle stack 128 words (512 bytes), all inside the RTOS heap. The compiled V9
allocation code left **1,496 heap bytes** after modeled creation of those three
tasks in ARM emulation. The first physical run also measured 1,496 free heap bytes; observed unused
stack minima were LED 148 words, Work 210 words and idle 106 words before
active tracing. See validation/HARDWARE_RESULTS.md.
Do not add unused heap or unused task stacks to the 1,224-byte linker spare
figure as if they were interchangeable memory. Measure margins during the
first real recording; active-trace margins remain to be measured.

Release trace flash: **11,000 / 32,768 bytes**. Debug trace: **12,224 bytes**.
The debugger-compatible `uxTopUsedPriority` constant is retained in flash.

## Why the timestamp implementation changed

G030 has no TIM2 and no DWT cycle counter. Its TIM3 is 16-bit. We run TIM3 at
1 MHz and extend each overflow into `timestampHigh`, producing a 32-bit
microsecond timestamp. Pending overflow is handled during reads, even inside
a trace/RTOS critical section, and the previous interrupt mask is restored.

TIM3 overflow is priority 0; TIM17 HAL tick is priority 1; SysTick/PendSV use
the kernel's lowest priority. The overflow IRQ is intentionally not traced to
avoid recording from the timestamp source. It occurs every 65.536 ms. Never
disable interrupts for that entire interval: multiple missed wraps cannot be
reconstructed. The 32-bit result wraps after about 71.6 minutes; keep initial
captures short and verify time continuity. Probe/debug pauses freeze TIM3/TIM17
in the firmware as well as the supplied launch profiles, so attach cannot lose
multiple wraps while halted. Stop/start a recording after debugging.

## Move the folder and reproduce checks

Copy the whole folder, including `.vscode`, `vendor`, `common`, `projects`,
`debug`, `openocd` and `tests`. Generated `build` output is optional.

```powershell
python check_package.py --relocation-build
python configure_vscode.py --force
```

The first command builds both images and profiles in a temporary folder away
from the original sources. The second regenerates host paths on another PC;
back up custom VS Code edits before using `--force`.

The optional ARM logic tests need `unicorn==2.1.4` as a **host development**
package, not a firmware dependency:

```powershell
python -m pip install unicorn==2.1.4
python tests/test_timestamp_arm.py
```

Validation records identify what was checked. First G030/Pico programming,
RTOS execution and RTT console checks passed; live SystemView capture is pending. Library revisions and licenses are recorded
in `vendor/provenance.json`. The board schematic was checked at WeAct commit
`f692e4e2e853ae9610aa337e2222c6d6d73416d8`.

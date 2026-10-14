"""Build the tested four-page guide from local validation and capture artifacts.

Documentation tools only: reportlab and matplotlib. Firmware builds need neither.
"""
from pathlib import Path
import csv
import gzip
import json
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                               TableStyle, PageBreak, Image, KeepTogether)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/WeAct_G030_Pico_SystemView_Quickstart.pdf"
TEMP = ROOT / "tmp/pdfs"
TEMP.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
analysis = json.loads((ROOT / "validation/systemview_capture_analysis.json").read_text())
capture = ROOT / analysis["recording"]
event_csv = capture.with_name(capture.stem + "_events.csv")
if event_csv.exists():
    event_source = event_csv.open(encoding="utf-8-sig", newline="")
else:
    event_source = gzip.open(str(event_csv) + ".gz", "rt", encoding="utf-8-sig", newline="")
with event_source:
    events = list(csv.DictReader(event_source))
navy, teal, grey = "#15394E", "#007E87", "#506373"

fig, axes = plt.subplots(2, 1, figsize=(8, 3.8), constrained_layout=True)
for name, row, colour in [("LED toggle", 0, teal), ("Work burst", 1, "#D26A37")]:
    starts = [int(e["timestampint"]) / 1e6 for e in events if e["event"] == "Start " + name]
    stops = [int(e["timestampint"]) / 1e6 for e in events if e["event"] == "Stop " + name]
    for begin, end in zip(starts, stops):
        if begin <= 1.2:
            axes[0].vlines(begin, row - .25, row + .25, color=colour, linewidth=2)
    if name == "Work burst":
        first = starts[0]
        axes[1].broken_barh([(0, (stops[0] - first) * 1000)], (.25, .5), facecolors=colour)
axes[0].set_yticks([0, 1], ["LED: 200 ms", "Work: 500 ms"])
axes[0].set_xlim(0, 1.2)
axes[0].set_xlabel("Time since this recording began (seconds)")
axes[0].grid(axis="x", alpha=.2)
axes[0].set_title("Actual recorded markers: two periodic tasks", loc="left", fontsize=12)
axes[1].set_xlim(-.2, 2.3)
axes[1].set_yticks([])
axes[1].set_xlabel("Elapsed time from Work burst marker start (milliseconds)")
axes[1].set_title("A measured Work burst: 2.007 ms", loc="left", fontsize=12)
axes[1].grid(axis="x", alpha=.2)
for axis in axes:
    axis.spines[["top", "right"]].set_visible(False)
fig.savefig(TEMP / "recorded_markers.png", dpi=180)
plt.close(fig)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleLocal", fontName="Helvetica-Bold", fontSize=23,
    leading=27, textColor=colors.HexColor(navy), spaceAfter=10))
styles.add(ParagraphStyle(name="HeadingLocal", fontName="Helvetica-Bold", fontSize=13,
    leading=17, textColor=colors.HexColor(teal), spaceBefore=10, spaceAfter=5))
styles.add(ParagraphStyle(name="BodyLocal", fontName="Helvetica", fontSize=9.6,
    leading=13.2, textColor=colors.HexColor(navy), spaceAfter=6))
styles.add(ParagraphStyle(name="SmallLocal", fontName="Helvetica", fontSize=8.5,
    leading=11.5, textColor=colors.HexColor(grey), spaceAfter=5))
styles.add(ParagraphStyle(name="CodeLocal", fontName="Courier", fontSize=9,
    leading=13, textColor=colors.HexColor(navy), spaceAfter=6))
story = []


def p(text, style="BodyLocal"):
    story.append(Paragraph(text, styles[style]))


def h(text):
    p(text, "HeadingLocal")


def page(title, intro):
    if story:
        story.append(PageBreak())
    p(title, "TitleLocal")
    p(intro)


def table(headers, rows, widths):
    values = [[Paragraph(str(c), styles["SmallLocal"]) for c in row]
              for row in [headers, *rows]]
    item = Table(values, colWidths=widths, repeatRows=1, hAlign="LEFT")
    item.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2F1F1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#C6D8DE")),
        ("LINEBELOW", (0, 0), (-1, 0), .7, colors.HexColor(teal)),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7)]))
    story.extend([item, Spacer(1, 8)])


def step(number, title, body):
    h(str(number) + ". " + title)
    p(body)


page("Your working SystemView demo", "WeAct STM32G030F6P6 + RP2040/yapicoprobe + VS Code. Tested 13 October 2026.")
p("This guide belongs to the <b>Duke-derived FreeRTOS/SystemView project</b>, in the folder <b>weact_g030_systemview</b>. Your hardware-test Blinky and PX-fwlib port are separate projects.")
table(["What has been proved", "Evidence"], [
    ["Build, flash and RTOS execution", "Verified flash/readback; LEDtask, WorkTask and IDLE seen; counters advance; failure flags zero."],
    ["RTT text inside VS Code", "User confirmed repeated WorkTask messages in channel 0."],
    ["Real target event recording", "Five-second .SVDat decoded by SystemView: 20,273 events, zero reported overflow events."],
    ["Live SystemView display", "User confirmed a filling timeline and supplied a screenshot showing 149,406 events at 36.903 seconds."]
], [190, 328])
h("One probe connection, two useful channels")
p("VS Code starts OpenOCD and owns the Pico's SWD connection. RTT uses buffers in STM32 RAM. Channel 0 carries text; channel 1 carries binary SystemView events. No COM port or UART wires are needed for this route.")
p("<b>STM32 RAM -&gt; SWD -&gt; Pico USB -&gt; OpenOCD -&gt; Python IP bridge -&gt; SystemView</b>")
p("The bridge supplies SystemView's 32-byte IP handshake. A raw OpenOCD RTT socket alone is insufficient. The STM32 needs no network stack. The helper uses Python's standard library and does not build, flash, or open a second debugger.")
table(["Existing SWD wiring", "Connection"], [["Pico GP2", "WeAct CLK / PA14"], ["Pico GP3", "WeAct DIO / PA13"], ["GND", "Common ground; target powered at 3.3 V"]], [190, 328])
p("Leave the A14 button alone while probing: it shares SWCLK. Keep the working Cortex-Debug extension version. Host tools are external; all firmware libraries are bundled.", "SmallLocal")

page("Start it from VS Code", "Open weact_g030_systemview itself so the project's launch profiles and tasks apply.")
step(1, "Attach to the verified image", "Press Ctrl+Shift+D. Select <b>CMSIS-DAP: attach matching release trace image</b>, then F5. It uses the already-flashed release ELF. To rebuild and flash instead, select <b>Pico/yapicoprobe: SystemView demo (release)</b>.")
p("Trace profiles run firmware for 200 ms to initialize RTT, then pause. Press F5 again to continue. They now pause after initialization rather than at main. Keep the ELF matched to the image on the board.")
step(2, "Check the text channel", "Use Ctrl+Shift+P, then <b>Terminal: Switch Active Terminal</b>. Select <b>FreeRTOS RTT console</b>. Expect <font face='Courier'>WorkTask: burst complete</font> about every half-second. The nRF RTT output view is a different extension.")
step(3, "Start the channel-1 bridge", "Use Ctrl+Shift+P, <b>Tasks: Run Task</b>, then <b>SystemView: start channel 1 bridge</b>. Leave its task terminal running. It finds this project's active OpenOCD server and uses its existing SWD connection.")
p("If the bridge is already running in the current session, use that instance. A second instance reports an occupied port. Stop a bridge with Ctrl+C in its terminal before restarting it.")
step(4, "Open SystemView", "Run the task <b>SystemView: open application</b>, or open the installed SEGGER SystemView application. In SystemView choose <b>Target &gt; Recorder Configuration &gt; IP recorder</b>.")
table(["Setting", "Value"], [["IP address", "127.0.0.1"], ["Port", "19111"], ["Internal raw RTT port", "19022 - handled by the bridge, not entered in SystemView"]], [190, 328])
step(5, "Record a short baseline", "Keep the MCU running in VS Code. In SystemView choose <b>Target &gt; Start Recording</b>. Record 5-10 seconds, then choose <b>Target &gt; Stop Recording</b>. Close any information dialog with OK to view the timeline.")
p("F5 in VS Code continues debugging; F5 in SystemView starts recording. Use the menu commands initially. Keep the debug session and bridge running while recording.", "SmallLocal")

page("Read your actual timing", "This figure is generated from the saved WeAct hardware events, not a SEGGER sample or a simulated schedule.")
story.append(Image(str(TEMP / "recorded_markers.png"), width=518, height=230))
table(["Measured item", "Five-second capture"], [
    ["LED toggle period", "Median 200.000 ms; range 197.821-202.179 ms"],
    ["Work burst period", "499.992-500.008 ms"],
    ["Work burst marker duration", "2.007 ms for all 10 observed bursts"],
    ["Recorded idle share", "96.89% in the decoded Contexts export"],
    ["Overflow/lost events", "Zero reported in this clip; timestamps monotonic"]
], [230, 288])
h("Why the LED has a small timing variation")
p("WorkTask has priority 2; LEDtask has priority 1. When both are ready, WorkTask runs first. The LED can wait for that burst, then return to its fixed periodic schedule. The observed timing variation is consistent with this priority relationship.")
p("Use <b>Window &gt; Timeline</b>, <b>Window &gt; Context View</b>, and <b>Window &gt; CPU Load</b> in SystemView. Zoom with the mouse wheel. Select a Work burst start event and compare it with its stop event. Use the event filter to hide frequent tick interrupts when learning the task pattern.")
p("Timestamps come from TIM3 at 1 MHz, so one count is 1 microsecond. The firmware clock setting is 64 MHz. These are instrumented firmware measurements, not an external clock calibration.", "SmallLocal")

page("Save, replay and change one thing", "Keep a baseline trace and matching firmware before experimenting.")
step(1, "Save your recording", "In SystemView use <b>File &gt; Save Recording</b>. Store the .SVDat in this project's <b>captures</b> folder. In File &gt; Load Recording, you can replay it later with no hardware connection.")
p("The verified baseline is <b>captures/2026-10-13/WeAct_G030_RTT_195317.SVDat</b>. Its Contexts CSV and validation/systemview_capture_analysis.json preserve measurements. A matching release ELF is saved locally in the same capture folder. A compressed event CSV is included; the uncompressed export stays local.")
table(["Active-trace memory observation", "Remaining"], [["RTOS heap", "1,496 bytes"], ["LED task stack", "140 words = 560 bytes"], ["Work task stack", "202 words = 808 bytes"], ["Idle task stack", "106 words = 424 bytes"], ["RAM outside linker reservations", "1,224 bytes; not the same pool as free RTOS heap"]], [330, 188])
p("The release firmware uses 11,000 of 32,768 flash bytes and reserves 6,968 of 8,192 RAM bytes. Stack figures are observed unused minima, not worst-case proof. Interrupt/main stack high-water was not measured.", "SmallLocal")
step(2, "Make one timing experiment", "Edit <b>projects/systemview_demo/Inc/demo.h</b>. Change LED period from 200 to 100 ms, or work burst from 2000 to 4000 microseconds. Rebuild/reflash the release demo and save a second trace. Compare it with the baseline.")
table(["Symptom", "First action"], [["Rcmd 01 / RTT start error", "End the old debug session and start the updated profile; RTT must initialize first."], ["No live events", "Continue the MCU; check bridge task and IP recorder 127.0.0.1:19111."], ["Timeline hidden", "Close any dialog, use Window > Timeline, then zoom into recorded activity."], ["Overflow indication", "Keep a short clip; check 5 ms polling and host load before trusting measurements."]], [200, 318])
p("Progress and limits: docs/SYSTEMVIEW_PROGRESS.md and validation/*.json. Transport protocol reference: github.com/rgrr/yapicoprobe/blob/master/src/net/net_sysview.c. Recorder controls: doc.segger.com/UM08027_SystemView.html.", "SmallLocal")


def footer(canvas, document):
    canvas.setStrokeColor(colors.HexColor(teal))
    canvas.setLineWidth(2)
    canvas.line(47, 752, 565, 752)
    canvas.setFillColor(colors.HexColor(grey))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(47, 27, "WEACT G030 | TESTED SYSTEMVIEW QUICK START | 13 OCTOBER 2026")
    canvas.drawRightString(565, 27, str(document.page) + " / 4")


document = SimpleDocTemplate(str(OUT), pagesize=(612, 792), leftMargin=47,
    rightMargin=47, topMargin=54, bottomMargin=65,
    title="WeAct G030 Pico SystemView - Tested Quick Start")
document.build(story, onFirstPage=footer, onLaterPages=footer)
shutil.copy2(OUT, ROOT / "docs" / OUT.name)
print(OUT)

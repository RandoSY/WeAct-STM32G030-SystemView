#!/usr/bin/env python3
"""Generate local VS Code configuration for the portable STM32 Arm GCC build."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT


def find_file(explicit, command, patterns=()):
    if explicit:
        result = Path(explicit).expanduser().resolve()
        if not result.is_file():
            raise RuntimeError("File does not exist: " + str(result))
        return result
    found = shutil.which(command)
    if found:
        return Path(found).resolve()
    for base, pattern in patterns:
        candidates = sorted(Path(base).glob(pattern), reverse=True)
        if candidates:
            return candidates[0].resolve()
    return None


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain-bin", default=os.environ.get("ARM_GCC_BIN"))
    parser.add_argument("--gdb", help="Optional separate arm-none-eabi-gdb executable")
    parser.add_argument("--openocd")
    parser.add_argument("--openocd-scripts")
    parser.add_argument("--jlink-server")
    parser.add_argument("--svd")
    parser.add_argument("--force", action="store_true", help="Replace generated launch/tasks/extension files")
    args = parser.parse_args()
    folder = REPO / ".vscode"
    settings_path = folder / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    exe = ".exe" if os.name == "nt" else ""
    gcc_explicit = str(Path(args.toolchain_bin) / ("arm-none-eabi-gcc" + exe)) if args.toolchain_bin else None
    gcc = find_file(gcc_explicit, "arm-none-eabi-gcc", [
        ("C:/Program Files (x86)/Arm", "*/bin/arm-none-eabi-gcc.exe"),
        ("C:/Program Files/Arm", "*/bin/arm-none-eabi-gcc.exe")])
    if not gcc:
        raise RuntimeError("Arm GCC not found; add it to PATH or pass --toolchain-bin")
    saved_gdb = settings.get("cortex-debug.gdbPath")
    gdb = (Path(args.gdb).expanduser().resolve() if args.gdb else
           Path(saved_gdb) if saved_gdb and Path(saved_gdb).is_file() else
           gcc.parent / ("arm-none-eabi-gdb" + exe))
    if not gdb.is_file():
        raise RuntimeError("Arm GDB missing: " + str(gdb))
    openocd = find_file(args.openocd, "openocd", [("C:/Openocd", "*/bin/openocd.exe")])
    if not openocd:
        raise RuntimeError("OpenOCD not found; add it to PATH or pass --openocd")
    if args.openocd_scripts:
        scripts = Path(args.openocd_scripts).expanduser().resolve()
    else:
        candidates = [openocd.parent.parent / "openocd/scripts",
                      openocd.parent.parent / "share/openocd/scripts"]
        scripts = next((p for p in candidates if (p / "target/stm32g0x.cfg").is_file()), None)
    if not scripts or not (scripts / "target/stm32g0x.cfg").is_file():
        raise RuntimeError("OpenOCD scripts not found; pass --openocd-scripts")
    jlink = find_file(args.jlink_server, "JLinkGDBServerCL", [
        ("C:/Program Files/SEGGER", "JLink*/JLinkGDBServerCL.exe")])
    svd = find_file(args.svd or str(ROOT / "debug/STM32G030.svd"), "__optional_stm32_svd__", [
        (Path.home() / "AppData/Local/Arm/Packs/Keil/STM32G0xx_DFP",
         "*/CMSIS/SVD/STM32G030.svd")])

    generated = [folder / name for name in ("launch.json", "tasks.json", "extensions.json")]
    if not args.force and any(p.exists() for p in generated):
        raise RuntimeError("VS Code files already exist; review them, then use --force to regenerate")
    folder.mkdir(exist_ok=True)
    settings.update({
        "armLessons.pythonPath": str(Path(sys.executable).resolve()),
        "armLessons.openocdScripts": str(scripts),
        "cortex-debug.armToolchainPath": str(gcc.parent),
        "cortex-debug.gdbPath": str(gdb),
        "cortex-debug.openocdPath": str(openocd),
        "C_Cpp.default.compilerPath": str(gcc),
        "C_Cpp.default.compileCommands": "${workspaceFolder}/build/debug/compile_commands.json",
        "C_Cpp.default.intelliSenseMode": "gcc-arm",
        "files.associations": {"*.h": "c"}
    })
    if jlink:
        settings["cortex-debug.JLinkGDBServerPath"] = str(jlink)
    if svd:
        settings["armLessons.svdFile"] = "${workspaceFolder}/debug/STM32G030.svd" if svd == (ROOT / "debug/STM32G030.svd").resolve() else str(svd)
    write_json(settings_path, settings)

    def task(label, target, profile, default=False):
        return {"label":label, "type":"process", "command":"${config:armLessons.pythonPath}",
                "args":["${workspaceFolder}/build.py",target,"--profile",profile],
                "options":{"cwd":"${workspaceFolder}","env":{"ARM_GCC_BIN":"${config:cortex-debug.armToolchainPath}"}},
                "problemMatcher":["$gcc"], "group":{"kind":"build","isDefault":default}}
    tasks = [task("G030: build all debug", "all", "debug", True),
             task("G030: build all release", "all", "release"),
             task("G030: build first blink", "blink", "debug"),
             task("G030: build trace debug", "systemview_demo", "debug"),
             task("G030: build trace release", "systemview_demo", "release")]
    write_json(folder / "tasks.json", {"version":"2.0.0", "tasks":tasks})
    configurations=[]
    def config(name, target, profile, probe="cmsis-dap", attach=False):
        value={"name":name,"type":"cortex-debug","request":"attach" if attach else "launch",
               "cwd":"${workspaceFolder}","servertype":"openocd","device":"STM32G030F6",
               "interface":"swd","executable":"${workspaceFolder}/build/"+profile+"/"+target+"/firmware.elf",
               "armToolchainPath":"${config:cortex-debug.armToolchainPath}",
               "gdbPath":"${config:cortex-debug.gdbPath}","serverpath":"${config:cortex-debug.openocdPath}",
               "searchDir":["${config:armLessons.openocdScripts}"],
               "configFiles":["${workspaceFolder}/openocd/"+probe+".cfg"],"rtos":"auto"}
        if svd: value["svdFile"]="${config:armLessons.svdFile}"
        if target == "systemview_demo":
            value["rttConfig"] = {"enabled":True, "address":"0x20000000",
                "searchSize":8192, "clearSearch":False, "polling_interval":50,
                "decoders":[{"port":0, "type":"console",
                    "label":"FreeRTOS RTT console", "inputmode":"disabled"}]}
        if not attach:
            value.update({"runToEntryPoint":"main", "preLaunchTask":"G030: build first blink" if target=="blink" else "G030: build trace "+profile,
                          "postLaunchCommands":["set {unsigned int}0x40015808 = {unsigned int}0x40015808 | 0x00000002",
                                                "set {unsigned int}0x4001580c = {unsigned int}0x4001580c | 0x00040000"]})
        configurations.append(value)
    config("Pico/yapicoprobe: SystemView demo (release)","systemview_demo","release")
    config("Pico/yapicoprobe: first blink", "blink", "debug")
    config("Pico/yapicoprobe: inspect trace demo (debug)", "systemview_demo", "debug")
    config("CMSIS-DAP: attach matching release trace image", "systemview_demo", "release", attach=True)
    config("External ST-Link: first blink", "blink", "debug", "stlink")
    config("External ST-Link: trace demo (debug)", "systemview_demo", "debug", "stlink")
    config("Old ST-Link clone: legacy fallback", "systemview_demo", "debug", "stlink-legacy")
    write_json(folder / "launch.json", {"version":"0.2.0", "configurations":configurations})
    write_json(folder / "extensions.json", {"recommendations":["ms-vscode.cpptools","marus25.cortex-debug",
        "mcu-debug.memory-view","mcu-debug.peripheral-viewer","mcu-debug.rtos-views","ms-vscode.vscode-serial-monitor"]})
    print("Configured standalone WeAct STM32G030F6P6 in " + str(folder))
    print("GDB: " + str(gdb))
    print("OpenOCD: " + str(openocd))
    print("No probe connection, reset or flashing was performed.")


if __name__ == "__main__":
    try: main()
    except (RuntimeError,OSError,ValueError) as error:
        print("ERROR: " + str(error),file=sys.stderr)
        sys.exit(1)

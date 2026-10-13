#!/usr/bin/env python3
"""Portable Arm GCC build for all STM32 tutorial programs (Python standard library)."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT  # All inputs must stay within this standalone package.
BUILD_ROOT = ROOT / "build"
BUILD = BUILD_ROOT / "debug"
MANIFEST = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
CPU = ["-mcpu=cortex-m0plus", "-mthumb", "-mfloat-abi=soft"]

# STM32G030 vector indices, matching the reference manual/startup table.
VECTORS = {'Reset_Handler': 1, 'NMI_Handler': 2, 'HardFault_Handler': 3, 'SVC_Handler': 11, 'PendSV_Handler': 14, 'SysTick_Handler': 15, 'WWDG_IRQHandler': 16, 'RTC_TAMP_IRQHandler': 18, 'FLASH_IRQHandler': 19, 'RCC_IRQHandler': 20, 'EXTI0_1_IRQHandler': 21, 'EXTI2_3_IRQHandler': 22, 'EXTI4_15_IRQHandler': 23, 'DMA1_Channel1_IRQHandler': 25, 'DMA1_Channel2_3_IRQHandler': 26, 'DMA1_Ch4_5_DMAMUX1_OVR_IRQHandler': 27, 'ADC1_IRQHandler': 28, 'TIM1_BRK_UP_TRG_COM_IRQHandler': 29, 'TIM1_CC_IRQHandler': 30, 'TIM3_IRQHandler': 32, 'TIM14_IRQHandler': 35, 'TIM16_IRQHandler': 37, 'TIM17_IRQHandler': 38, 'I2C1_IRQHandler': 39, 'I2C2_IRQHandler': 40, 'SPI1_IRQHandler': 41, 'SPI2_IRQHandler': 42, 'USART1_IRQHandler': 43, 'USART2_IRQHandler': 44}


def run(arguments):
    result = subprocess.run([str(a) for a in arguments], cwd=ROOT,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(result.stdout + "\nCommand failed: " + subprocess.list2cmdline(
            [str(a) for a in arguments]))
    if "warning:" in result.stdout.lower():
        print(result.stdout, end="", flush=True)
    return result.stdout


def tools_for(directory):
    gcc = (Path(directory).expanduser().resolve() / ("arm-none-eabi-gcc.exe" if os.name == "nt"
           else "arm-none-eabi-gcc")) if directory else shutil.which("arm-none-eabi-gcc")
    if not gcc or not Path(gcc).is_file():
        raise RuntimeError("Install Arm GNU Toolchain and add bin to PATH, or use --toolchain-bin.")
    gcc = Path(gcc).resolve()
    suffix = gcc.suffix
    tools = {name: gcc.parent / ("arm-none-eabi-" + name + suffix)
             for name in ("gcc", "objcopy", "nm")}
    for tool in tools.values():
        if not tool.is_file():
            raise RuntimeError("Missing tool: " + str(tool))
    return tools


def inputs_for(name):
    project = MANIFEST[name]
    app = ROOT / "projects" / name
    drivers = ROOT / "vendor/STM32G0xx_HAL_Driver"
    includes = [app / "Inc", ROOT / "common", drivers / "Inc", drivers / "Inc/Legacy",
                ROOT / "vendor/CMSIS_Device_G0/Include", ROOT / "vendor/CMSIS_Core/Include"]
    sources = sorted((app / "Src").glob("*.c"))
    sources += [ROOT / "common/board.c", ROOT / "vendor/CMSIS_Device_G0/Source/Templates/system_stm32g0xx.c"]
    sources += [drivers / "Src" / filename for filename in project["drivers"]]
    if project["stdio"]: sources.append(ROOT / "common/gcc_uart.c")
    if project["rtos"]:
        rtos = ROOT / "vendor" / ("FreeRTOS_SystemView" if project["trace"] else "FreeRTOS")
        includes += [rtos / "portable/GCC/ARM_CM0", rtos / "include", rtos / "CMSIS_RTOS"]
        sources += [rtos / "portable/GCC/ARM_CM0/port.c", ROOT / "common/rtos_diagnostics.c"]
        sources += [rtos / filename for filename in (
            "tasks.c", "queue.c", "list.c", "portable/MemMang/heap_1.c")]
    if project["trace"]:
        sources.append(ROOT / "common/timestamp.c")
        includes += [ROOT / "vendor/SystemView/SEGGER", ROOT / "vendor/SystemView/SYSVIEW",
                     ROOT / "vendor/SystemView/Sample/FreeRTOSV9", ROOT / "vendor/RTT/RTT",
                     ROOT / "vendor/SystemView/Config"]
        sources += [ROOT / "vendor/SystemView/SYSVIEW/SEGGER_SYSVIEW.c",
                    ROOT / "vendor/SystemView/Sample/FreeRTOSV9/SEGGER_SYSVIEW_FreeRTOS.c",
                    ROOT / "vendor/RTT/RTT/SEGGER_RTT.c"]
    sources.append(ROOT / "common/startup_stm32g030.S")
    for path in includes + sources:
        if not path.resolve().is_relative_to(ROOT.resolve()):
            raise RuntimeError("Input outside standalone package: " + str(path))

    return project, includes, sources


def image_report(name, tools):
    project = MANIFEST[name]
    output = BUILD / name
    binary = (output / "firmware.bin").read_bytes()
    symbols = {}
    for line in run([tools["nm"], "-n", output / "firmware.elf"]).splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]+)\s+(\S)\s+(\S+)", line)
        if match:
            symbols[match[3]] = (int(match[1], 16), match[2])
    if not 184 <= len(binary) <= 32768 or struct.unpack_from("<I", binary)[0] != 0x20002000:
        raise RuntimeError(name + ": invalid image length or initial stack")
    for handler in ["Reset_Handler", *project["handlers"]]:
        address, kind = symbols.get(handler, (0, "?"))
        if kind != "T" or struct.unpack_from("<I", binary, VECTORS[handler] * 4)[0] != (address | 1):
            raise RuntimeError(name + ": missing implementation or bad Thumb vector for " + handler)
    required = ["main", "SystemInit"]
    if project["stdio"]:
        required += ["_write", "_sbrk", "gcc_uart_stdio_init"]
    if project["rtos"]:
        required += ["StartLEDtask", "StartWorkTask", "HAL_InitTick", "xPortSysTickHandler",
                     "vApplicationMallocFailedHook",
                     "vApplicationStackOverflowHook"]
    if project["rtos"]:
        address = symbols.get("uxTopUsedPriority", (0, "?"))[0] - 0x08000000
        if not (0 <= address <= len(binary) - 4) or struct.unpack_from("<I", binary, address)[0] != 6:
            raise RuntimeError(name + ": missing OpenOCD priority compatibility constant")
    for symbol in required:
        if symbols.get(symbol, (0, "?"))[1] != "T":
            raise RuntimeError(name + ": missing symbol " + symbol)
    if project["trace"]:
        for symbol in ("_SEGGER_RTT", "SEGGER_SYSVIEW_Init", "SEGGER_SYSVIEW_Conf",
                       "SystemView_GetTimestamp", "SYSVIEW_AddTask"):
            if symbol not in symbols:
                raise RuntimeError(name + ": missing trace symbol " + symbol)
    ram = symbols["_reserved_end"][0] - 0x20000000
    if ram > 8192 or symbols["_stack_limit"][0] < symbols["_heap_end"][0]:
        raise RuntimeError(name + ": image exceeds RAM/stack budget")
    data_size = symbols["_edata"][0] - symbols["_sdata"][0]
    data_offset = symbols["_sidata"][0] - 0x08000000
    if data_offset < 0 or data_offset + data_size > len(binary):
        raise RuntimeError(name + ": initialized RAM data missing from flash image")
    link_map = (output / "firmware.map").read_text(encoding="utf-8", errors="replace")
    if re.search(r"RVDS|MDK-ARM|uvproj|uvopt|microlib|\b__main\b", link_map, re.I):
        raise RuntimeError(name + ": Keil dependency in linked image")
    report = {"target": name, "flash_bytes": len(binary), "ram_reserved_bytes": ram,
              "flash_limit": 32768, "ram_limit": 8192,
              "newlib_heap_bytes": symbols["_heap_end"][0] - symbols["_heap_start"][0],
              "msp_stack_bytes": symbols["_stack_size"][0],
              "verified_vectors": ["Reset_Handler", *project["handlers"]],
              "binary_sha256": hashlib.sha256(binary).hexdigest(), "hardware_tested": False}
    report["ram_headroom_bytes"] = 8192 - ram
    report["flash_headroom_bytes"] = 32768 - len(binary)
    if project["trace"]:
        report.update({"systemview_buffer_bytes": 1024, "freertos_heap_bytes": 4096,
                       "timestamp_hz": 1000000, "timestamp_bits": 32,
                       "runtime_stack_high_water_verified": False, "timestamp_source": "TIM3 16-bit plus overflow extension"})
    (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def build_one(name, tools, compiler_version, jobs, rebuild, profile):
    project, includes, sources = inputs_for(name)
    output = BUILD / name
    output.mkdir(parents=True, exist_ok=True)
    flags = CPU + ["-std=gnu99", "-Og" if profile == "debug" else "-Os", "-g3",
                   "-gdwarf-4", "-Wall", "-ffunction-sections",
                   "-fdata-sections", "-fstack-usage", "-DUSE_HAL_DRIVER", "-DSTM32G030xx"]
    flags += ["-D" + define for define in project["defines"]]
    flags += ["-DUSER_VECT_TAB_ADDRESS"]
    flags += ["-I" + str(path) for path in includes]
    objects = [output / (f"{index:02d}_" + source.stem + ".o") for index, source in enumerate(sources)]
    commands = [{"directory": str(ROOT), "file": str(source), "output": str(obj),
                 "arguments": [str(tools["gcc"]), *flags, "-c", str(source), "-o", str(obj)]}
                for source, obj in zip(sources, objects) if source.suffix == ".c"]
    (output / "compile_commands.json").write_text(json.dumps(commands, indent=2) + "\n", encoding="utf-8")
    # A conservative per-project content cache also tracks all headers and build logic.
    tracked = set(sources + [Path(__file__), ROOT / "projects.json", ROOT / "common/stm32g030f6.ld"])
    for include in includes:
        tracked.update(include.rglob("*.h"))
    digest = hashlib.sha256((compiler_version + str(tools["gcc"]) + repr(flags)).encode())
    for path in sorted(tracked):
        digest.update(str(path).encode())
        digest.update(path.read_bytes())
    signature = digest.hexdigest()
    cached = output / ".signature"
    artifacts = [output / ("firmware." + extension) for extension in ("elf", "bin", "hex", "map")]
    changed = rebuild or not cached.exists() or cached.read_text() != signature or not all(
        path.is_file() for path in artifacts)
    if changed:
        print("Building " + name, flush=True)

        def compile_source(pair):
            source, obj = pair
            run([tools["gcc"], *flags, "-c", source, "-o", obj])

        with ThreadPoolExecutor(max_workers=jobs) as pool:
            list(pool.map(compile_source, zip(sources, objects)))
        link = CPU + ["-nostartfiles", "--specs=nano.specs", "--specs=nosys.specs",
                      "-T", ROOT / "common/stm32g030f6.ld", "-Wl,--gc-sections", "-Wl,-z,noexecstack",
                      "-Wl,-Map=" + str(output.relative_to(ROOT) / "firmware.map"),
                      "-Wl,--defsym=__heap_size=" + ("512" if project["stdio"] else "0")]
        run([tools["gcc"], *link, *objects, "-Wl,--start-group", "-lc", "-lgcc", "-Wl,--end-group",
             "-o", output / "firmware.elf"])
        for fmt, extension in (("binary", "bin"), ("ihex", "hex")):
            run([tools["objcopy"], "-O", fmt, output / "firmware.elf", output / ("firmware." + extension)])
        cached.write_text(signature)
    report = image_report(name, tools)
    print(f"PASS {name}: flash {report['flash_bytes']}/32768, "
          f"RAM {report['ram_reserved_bytes']}/8192 bytes" + (" (cached)" if not changed else ""), flush=True)
    return report


def main():
    global BUILD
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", default="all", choices=["all", "list", "clean", *MANIFEST])
    parser.add_argument("--toolchain-bin", default=os.environ.get("ARM_GCC_BIN"))
    parser.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--profile", choices=["debug", "release"], default="debug",
                        help="debug: -Og; release: -Os. Both include symbols.")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    if args.target == "list":
        for name, project in MANIFEST.items():
            print(f"{name:24} {project['source_lesson']}")
        return
    if args.target == "clean":
        if BUILD_ROOT.exists():
            if BUILD_ROOT.is_symlink() or BUILD_ROOT.resolve().parent != ROOT:
                raise RuntimeError("Refusing to clean a build directory outside package")
            shutil.rmtree(BUILD_ROOT)
        print("Removed standalone build outputs")
        return
    tools = tools_for(args.toolchain_bin)
    BUILD = BUILD_ROOT / args.profile
    version = run([tools["gcc"], "--version"]).splitlines()[0]
    print(version, flush=True)
    reports = []
    for name in MANIFEST if args.target == "all" else [args.target]:
        reports.append(image_report(name, tools) if args.verify_only else build_one(
            name, tools, version, args.jobs, args.rebuild, args.profile))
    commands = []
    for path in sorted(BUILD.glob("*/compile_commands.json")):
        commands.extend(json.loads(path.read_text(encoding="utf-8")))
    (BUILD / "compile_commands.json").write_text(json.dumps(commands, indent=2) + "\n", encoding="utf-8")
    if args.target == "all":
        (BUILD / "validation.json").write_text(json.dumps({"compiler": version, "projects": reports},
            indent=2) + "\n", encoding="utf-8")
    print(f"{len(reports)} program(s) verified. Outputs: {BUILD}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, KeyError, subprocess.SubprocessError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        sys.exit(1)

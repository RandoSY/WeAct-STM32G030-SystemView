#!/usr/bin/env python3
"""Run compiled ARM timestamp and task-allocation code with simulated registers.

Optional development test: requires Unicorn, not needed to build the firmware.
It verifies wrap/interrupt-mask logic, not real clocks, IRQ latency or transport.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--unicorn-path', help='Optional directory containing unicorn')
args = parser.parse_args()
if args.unicorn_path: sys.path.insert(0, args.unicorn_path)
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PRIMASK

nm = shutil.which('arm-none-eabi-nm')
if not nm:
    settings = json.loads((ROOT/'.vscode/settings.json').read_text())
    nm = str(Path(settings['cortex-debug.armToolchainPath'])/'arm-none-eabi-nm.exe')
FLASH, RAM, TIM3 = 0x08000000, 0x20000000, 0x40000400
CNT, SR, RETURN = TIM3+0x24, TIM3+0x10, FLASH+0x7ffc
passed=[]
heap_results={}

for profile in ['debug','release']:
    folder = ROOT/'build'/profile/'systemview_demo'
    symbols={}
    listing=subprocess.check_output([nm,'-n',str(folder/'firmware.elf')],text=True)
    for line in listing.splitlines():
        m=re.fullmatch(r'([0-9a-fA-F]+)\s+\S\s+(\S+)',line)
        if m: symbols[m[2]]=int(m[1],16)

    def machine(high,low,pending,mask):
        u=Uc(UC_ARCH_ARM, UC_MODE_THUMB|UC_MODE_MCLASS)
        u.mem_map(FLASH,0x8000);u.mem_write(FLASH,(folder/'firmware.bin').read_bytes())
        u.mem_map(RAM,0x2000);u.mem_map(0x40000000,0x2000)
        data_start=symbols['_sdata'];data_size=symbols['_edata']-data_start
        if data_size:
            image=(folder/'firmware.bin').read_bytes()
            offset=symbols['_sidata']-FLASH
            u.mem_write(data_start,image[offset:offset+data_size])
        for addr,value in [(symbols['timestampHigh'],high),(CNT,low),(SR,pending)]:
            u.mem_write(addr,struct.pack('<I',value))
        u.reg_write(UC_ARM_REG_SP,RAM+0x1f80)
        u.reg_write(UC_ARM_REG_PRIMASK,mask)
        return u

    def call(u,name):
        u.reg_write(UC_ARM_REG_LR,RETURN|1)
        u.emu_start(symbols[name]|1,RETURN,count=100000)
        assert u.reg_read(UC_ARM_REG_PC)==RETURN,(name,'Function did not return',hex(u.reg_read(UC_ARM_REG_PC)))
        return u.reg_read(UC_ARM_REG_R0)&0xffffffff

    for name,high,low,pending,mask,expected in [
        ('ordinary',0,123,0,0,123),
        ('already_masked',0x10000,42,0,1,0x1002a),
        ('last_tick_before_wrap',0,0xffff,0,0,0xffff),
        ('pending_wrap',0,3,1,0,0x10003),
        ('pending_wrap_while_masked',0,3,1,1,0x10003),
        ('serviced_wrap',0x10000,3,0,0,0x10003),
        ('32_bit_rollover',0xffff0000,3,1,1,3)]:
        u=machine(high,low,pending,mask)
        actual=call(u,'SystemView_GetTimestamp')
        assert actual==expected,(profile,name,hex(actual),hex(expected))
        assert u.reg_read(UC_ARM_REG_PRIMASK)==mask,(profile,name,'PRIMASK altered')
        passed.append(profile+':'+name)

    # Inject a timer overflow after the first CNT read but before SR is read.
    u=machine(0,0xffff,0,0)
    def inject_wrap(engine,access,address,size,value,user):
        if address==SR:
            engine.mem_write(CNT,struct.pack('<I',4));engine.mem_write(SR,struct.pack('<I',1))
    hook=u.hook_add(UC_HOOK_MEM_READ,inject_wrap)
    assert call(u,'SystemView_GetTimestamp')==0x10004,profile+': rollover race'
    u.hook_del(hook);passed.append(profile+':wrap_between_counter_and_flag')

    u=machine(0,9,1,0);call(u,'TIM3_IRQHandler')
    assert struct.unpack('<I',u.mem_read(symbols['timestampHigh'],4))[0]==0x10000
    assert struct.unpack('<I',u.mem_read(SR,4))[0]&1==0
    assert call(u,'SystemView_GetTimestamp')==0x10009
    passed.append(profile+':overflow_interrupt_service')
    u=machine(0x10000,17,0,0);call(u,'TIM3_IRQHandler')
    assert struct.unpack('<I',u.mem_read(symbols['timestampHigh'],4))[0]==0x10000
    passed.append(profile+':interrupt_without_update')

    # Execute the real V9 allocator/task creation code with tracing inactive.
    # This checks allocation fit, not scheduler execution or runtime stacks.
    u=machine(0,0,0,0)
    for i,(function,name,depth,priority) in enumerate([
        ('StartLEDtask','LEDtask',192,1),('StartWorkTask','WorkTask',256,2),
        ('prvIdleTask','IDLE',128,0)]):
        name_address=FLASH+0x7100+i*64
        u.mem_write(name_address,name.encode()+b'\0')
        u.reg_write(UC_ARM_REG_SP,RAM+0x1f80)
        for register,value in [(UC_ARM_REG_R0,symbols[function]|1),
                               (UC_ARM_REG_R1,name_address),(UC_ARM_REG_R2,depth),
                               (UC_ARM_REG_R3,0)]:u.reg_write(register,value)
        u.mem_write(RAM+0x1f80,struct.pack('<II',priority,RAM+0x1fe0))
        assert call(u,'xTaskCreate')==1,(profile,name,'allocation failed')
    free=call(u,'xPortGetFreeHeapSize')
    assert free>=1024,(profile,'insufficient modeled heap margin',free)
    heap_results[profile]=free
    passed.append(profile+':three_task_allocations_fit')

report={'result':'PASS','cases':passed,'compiled_arm_code':True,
        'modeled_heap_free_bytes_after_three_tasks':heap_results,
        'physical_peripherals_emulated':False,'hardware_tested':False,
        'scope':'timestamp arithmetic, pending-overflow race, interrupt service, PRIMASK preservation and three startup task allocations'}
folder=ROOT/'validation';folder.mkdir(exist_ok=True)
(folder/'timestamp_arm_tests.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS:',len(passed),'compiled ARM timestamp/allocation cases')

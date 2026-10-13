#!/usr/bin/env python3
"""Check source containment, exact G030 startup, VS Code, and optional relocation."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import build

ROOT=Path(__file__).resolve().parent

def check():
    count=0
    for path in ROOT.rglob('*'):
        if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):
            raise RuntimeError('A portable package must not contain links: '+str(path))
    for name in build.MANIFEST:
        _,includes,sources=build.inputs_for(name)
        for path in includes+sources:
            if not path.exists() or not path.resolve().is_relative_to(ROOT):
                raise RuntimeError('Missing/external firmware input: '+str(path))
        count+=sum(p.suffix=='.c' for p in sources)
    ours=(ROOT/'common/startup_stm32g030.S').read_text()
    official=(ROOT/'vendor/CMSIS_Device_G0/Source/Templates/gcc/startup_stm32g030xx.s').read_text()
    def words(s):return re.findall(r'\.word\s+(\w+)',s.split('g_pfnVectors:',1)[1].split('.size',1)[0])
    table=words(ours)
    if table!=words(official) or len(table)!=46:raise RuntimeError('G030 startup mismatch')
    if table[31]!='0':raise RuntimeError('G030 has no TIM2 vector')
    for name,index in build.VECTORS.items():
        if table[index]!=name:raise RuntimeError('Incorrect image checker index: '+name)
    tasks=json.loads((ROOT/'.vscode/tasks.json').read_text())['tasks']
    labels={x['label'] for x in tasks}
    configs=json.loads((ROOT/'.vscode/launch.json').read_text())['configurations']
    for cfg in configs:
        if cfg['device']!='STM32G030F6':raise RuntimeError('Wrong debugger device')
        if cfg.get('preLaunchTask') not in labels|{None}:raise RuntimeError('Missing build task')
        if cfg['request']=='attach' and 'preLaunchTask' in cfg:raise RuntimeError('Attach must not rebuild')
        for name in cfg['configFiles']:
            if not Path(name.replace('${workspaceFolder}',str(ROOT))).is_file():raise RuntimeError('Missing probe configuration')
    return {'result':'PASS','programs':len(build.MANIFEST),'compiler_source_entries':count,
            'external_firmware_inputs':[],'vectors_match_pinned_ST_G030':True,
            'debug_configurations':len(configs),'hardware_tested':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--relocation-build',action='store_true')
    parser.add_argument('--toolchain-bin')
    args=parser.parse_args(); report=check()
    if args.relocation_build:
        with tempfile.TemporaryDirectory(prefix='WeAct G030 moved ') as temporary:
            copy=Path(temporary)/'Standalone SystemView example'
            shutil.copytree(ROOT,copy,ignore=shutil.ignore_patterns('build','validation','__pycache__','.git'))
            for profile in ['debug','release']:
                command=[sys.executable,str(copy/'build.py'),'all','--profile',profile]
                if args.toolchain_bin:command+=['--toolchain-bin',args.toolchain_bin]
                subprocess.run(command,cwd=copy,check=True)
                database=json.loads((copy/'build'/profile/'compile_commands.json').read_text())
                for entry in database:
                    paths=[entry['directory'],entry['file'],entry['output']]
                    paths += [x[2:] for x in entry['arguments'] if x.startswith('-I')]
                    if any(not Path(p).resolve().is_relative_to(copy.resolve()) for p in paths):
                        raise RuntimeError('Relocated build still references original sources')
            report['relocated_debug_and_release']='PASS'
    folder=ROOT/'validation';folder.mkdir(exist_ok=True)
    (folder/'standalone_check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    try: main()
    except (RuntimeError,OSError,KeyError,subprocess.SubprocessError) as error:
        print('ERROR: '+str(error),file=sys.stderr);sys.exit(1)

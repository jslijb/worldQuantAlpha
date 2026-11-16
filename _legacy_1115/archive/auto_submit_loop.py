# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 自动重试循环：平台自相关服务停摆时定期探测，恢复后自动提交所有排队候选
import subprocess, time, sys, os, json, requests

PY = r'D:/ProgramData/Miniforge3/envs/bigmodel/python.exe'
PREFIXES = ['w112_', 'w114_', 'w115_', 'w116_', 'w118_', 'w119_']
# 探针用「已提交」的 alpha（自相关数据已存在且稳定），比未提交的新仿真可靠
PROBES = ['akLmmvPW', 'kqVp6wnO', 'npKGgKLw']   # w116_e / w116_d / w108_e（均已 ACTIVE）

def service_ok():
    try:
        s = requests.Session()
        s.auth = tuple(json.load(open('brain_credentials.txt')))
        if s.post('https://api.worldquantbrain.com/authentication').status_code != 201:
            return False
        for aid in PROBES:
            try:
                r = s.get(f'https://api.worldquantbrain.com/alphas/{aid}/correlations/self')
                if r.status_code == 200 and len(r.content) > 0:
                    j = r.json()
                    if j.get('records'):
                        s.close()
                        return True
            except Exception:
                continue
        s.close()
        return False
    except Exception as e:
        print('probe err', e, flush=True)
        return False

def ledger_count():
    import csv
    try:
        rows = list(csv.DictReader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig')))
        return len([r for r in rows if r.get('dateSubmitted')])
    except Exception:
        return -1

if __name__ == '__main__':
    LOG = 'data/alpha_quality_analysis/auto_submit_loop.log'
    def log(msg):
        line = msg
        print(line, flush=True)
        try:
            with open(LOG, 'a', encoding='utf-8') as f:
                f.write(time.strftime('%Y-%m-%d %H:%M:%S ') + line + '\n')
        except Exception:
            pass
    log(f'auto_submit_loop 启动，探针 {PROBES} | 台账有效提交 {ledger_count()}')
    for rnd in range(1, 121):   # 最多 ~20 小时
        ok = service_ok()
        log(f'[{time.strftime("%H:%M:%S")}] 第{rnd}轮 服务状态: ' + ('UP' if ok else 'DOWN') + f' | 台账 {ledger_count()}')
        if ok:
            for pre in PREFIXES:
                try:
                    subprocess.run([PY, 'src/submit/submit_v2.py', f'auto{rnd}', pre], timeout=3600)
                except Exception as e:
                    log(f'run err {pre} {e}')
            log(f'[{time.strftime("%H:%M:%S")}] 一轮提交完毕，台账 {ledger_count()}')
        time.sleep(600)
    log('auto_submit_loop 结束')

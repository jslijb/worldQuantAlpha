# -*- coding: utf-8 -*-
"""Brain 平台统一客户端 —— 所有脚本只 import 这一个，不再各自写登录。

为什么要这个文件：
    _autologs/ 里 257 个脚本自己写登录、276 个自己读凭据、74 个自己写 say()。
    每次改接口都要改几百个文件。这个类把那些重复收在一处。

设计原则：
    1. 错误明示，不静默 —— 今天 mine_from_spec 静默丢了 10 条模拟，查了半天
    2. 不猜阈值 —— 门槛值一律从 core.knowledge 取
    3. 可后台 —— 长任务用 run(codes) 批量，调用方决定并发

用法：
    from src.core.session import Brain
    b = Brain()
    a = b.alpha('O0WEE6zJ')
    ok, detail = b.submit('xxxx', dry_run=True)
"""
import io
import json
import os
import sys
import time

import requests

_ROOT = None
for _d in [os.path.dirname(os.path.abspath(__file__))] + \
          [os.path.dirname(os.path.abspath(__file__))]:
    pass  # 占位，真正的项目根在下面用 credentials 定位

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = 'https://api.worldquantbrain.com'
DEFAULT_SETTINGS_FILE = os.path.join(
    PROJ, 'data', 'alpha_quality_analysis', 'mined', 'le8T2_t0.05_03.json')


def _log_path():
    d = os.path.join(PROJ, '_autologs')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '_brain_client.log')


def say(msg):
    """统一日志：同时打屏和写 _autologs/_brain_client.log。"""
    line = '%s %s' % (time.strftime('%m-%d %H:%M:%S'), msg)
    print(line, flush=True)
    try:
        io.open(_log_path(), 'a', encoding='utf-8').write(line + '\n')
    except Exception:
        pass


class BrainError(Exception):
    pass


class Brain:
    """已认证的 Brain 客户端。构造即登录。"""

    def __init__(self, timeout=60, verbose=False):
        self.timeout = timeout
        self.verbose = verbose
        self.s = requests.Session()
        cred = os.path.join(PROJ, 'brain_credentials.txt')
        if not os.path.exists(cred):
            raise BrainError('找不到凭据文件: %s' % cred)
        u, p = json.load(io.open(cred, encoding='utf-8'))[:2]
        for attempt in range(3):
            r = self.s.post(API + '/authentication', auth=(u, p), timeout=self.timeout)
            if r.status_code == 201:
                return
            time.sleep(3)
        raise BrainError('登录失败 http=%s' % r.status_code)

    # ---------- 读 ----------
    def alpha(self, aid):
        """取 alpha 详情。返回 dict；失败抛 BrainError。"""
        r = self.s.get('%s/alphas/%s' % (API, aid), timeout=self.timeout)
        if r.status_code != 200:
            raise BrainError('GET alpha %s http=%s' % (aid, r.status_code))
        return r.json()

    def check(self, aid, rounds=4, gap=4):
        """取平台检查项。首调常空，自动重试。

        返回 dict: {检查名: (result, value)}
        注意：每条恒有 SELF_CORRELATION=PENDING，不能用「全 PASS」判断。
        """
        for i in range(rounds):
            try:
                r = self.s.get('%s/alphas/%s/check' % (API, aid), timeout=self.timeout)
                j = r.json()
                cks = (j.get('is') or {}).get('checks') or []
                if cks:
                    return {c.get('name'): (c.get('result'), c.get('value')) for c in cks}
            except Exception as e:
                if self.verbose:
                    say('check %s 第 %d 轮异常 %s' % (aid, i + 1, e))
            time.sleep(gap)
        # 2026-11-13 修复：拿不到 checks 时必须返回 None，不能返回 {}。
        # 空 dict 会被调用方当成「全 PASS」，导致提交被 403 拒（实测 VkNJLK8G）。
        return None

    def fails(self, aid, **kw):
        """只返回 FAIL 项列表 [(name, value)]。

        GET /check 拿不到 body 时返回 CHECK_UNAVAILABLE，绝不假装「零 FAIL」。
        """
        m = self.check(aid, **kw)
        if m is None:
            return [('CHECK_UNAVAILABLE', None)]
        return [(k, v[1]) for k, v in m.items() if v[0] == 'FAIL']

    def fields(self, dataset=None, region='USA', delay=1, universe='TOP3000',
               order='-dateCreated', min_cov=0.0, max_alpha=None, limit=500):
        """拉字段清单。

        order 默认 -dateCreated = 按上线上线时间倒序（论坛验证的正确找法）。
        只按 alphaCount==0 找会撞死字段，必须先看新不新。
        """
        out, off = [], 0
        while off < limit:
            u = ('%s/data-fields?instrumentType=EQUITY&region=%s&delay=%s&universe=%s'
                 '&limit=50&offset=%d' % (API, region, delay, universe, off))
            if dataset:
                u += '&dataset.id=%s' % dataset
            if order:
                u += '&order=%s' % order
            r = None
            for _ in range(3):
                try:
                    r = self.s.get(u, timeout=self.timeout)
                    if r.status_code == 200:
                        break
                except Exception:
                    pass
                time.sleep(3)
            if not r or r.status_code != 200:
                break
            j = r.json()
            res = j.get('results') or []
            for x in res:
                f = dict(id=x.get('id'), type=x.get('type'), cov=x.get('coverage'),
                         users=x.get('userCount'), alphas=x.get('alphaCount'),
                         created=x.get('dateCreated'),
                         dataset=(x.get('dataset') or {}).get('id'))
                if (f['cov'] or 0) < min_cov:
                    continue
                if max_alpha is not None and (f['alphas'] or 0) > max_alpha:
                    continue
                out.append(f)
            off += 50
            if off >= (j.get('count') or 0):
                break
            time.sleep(0.4)
        return out

    # ---------- 写 ----------
    def submit(self, aid, dry_run=False, confirm_timeout=180):
        """提交 alpha。

        dry_run=True 时只查预检不提交（零配额）。
        返回 (ok, detail)。detail 里一定带原因，不静默。
        """
        d = {'alpha': aid}
        fails = self.fails(aid)
        d['fails'] = fails
        # GET /check 空 body 不代表通过；此时继续 POST，让平台回 403 完整真值
        # （403 不消耗 REGULAR_SUBMISSION 配额，实测 value 仍为 1）。
        hard = [f for f in fails if f[0] != 'CHECK_UNAVAILABLE']
        if hard:
            d['reason'] = 'PLATFORM_FAIL'
            return False, d
        if dry_run:
            d['reason'] = 'DRY_CHECK_UNAVAILABLE' if fails else 'DRY_RUN_PASS'
            return True, d

        r = self.s.post('%s/alphas/%s/submit' % (API, aid), timeout=120)
        d['post'] = r.status_code
        if r.status_code == 403:
            d['reason'] = 'REJECTED_403'
            try:
                b = r.json()
                d['body'] = (b.get('is') or {}).get('checks') or b
            except Exception:
                d['body'] = (r.text or '')[:400]
            return False, d
        if r.status_code not in (200, 201, 503):
            d['reason'] = 'HTTP_%s' % r.status_code
            return False, d

        # 回读确认：POST 201 不等于 ACTIVE，可能卡在平台审核
        deadline = time.time() + confirm_timeout
        while time.time() < deadline:
            time.sleep(6)
            try:
                a = self.alpha(aid)
            except Exception:
                continue
            st = a.get('status')
            if st and st != 'UNSUBMITTED':
                d.update(status=st, dateSubmitted=a.get('dateSubmitted'),
                         reason='ACTIVE' if st == 'ACTIVE' else st)
                return st == 'ACTIVE', d
        d['reason'] = 'POSTED_BUT_NOT_ACTIVE'
        return False, d

    def settings(self, **over):
        """默认回测参数（照抄一条已验证的 mined 记录），可覆盖 region/universe 等。"""
        try:
            base = json.load(io.open(DEFAULT_SETTINGS_FILE, encoding='utf-8'))['settings']
        except Exception:
            base = {
                'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000',
                'delay': 1, 'decay': 10, 'neutralization': 'SUBINDUSTRY',
                'truncation': 0.08, 'pasteurization': 'ON', 'unitHandling': 'VERIFY',
                'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False,
            }
        base = dict(base)
        base.update(over)
        return base

    def sim(self, code, settings=None, poll=90, gap=6, save_as=None, kind='REGULAR'):
        """跑一条模拟，返回 alpha 详情。

        不静默：任何失败都抛 BrainError 并带原因。
        """
        st = settings or self.settings()
        payload = {'type': kind, 'settings': st, 'regular': code}
        loc = None
        last = ''
        for _ in range(4):
            try:
                r = self.s.post(API + '/simulations', json=payload, timeout=120)
                if r.status_code == 201:
                    loc = r.headers.get('Location')
                    break
                last = '%s %s' % (r.status_code, (r.text or '')[:200])
                if r.status_code in (429, 403):
                    time.sleep(15)
                    continue
                raise BrainError('提交模拟失败 %s' % last)
            except BrainError:
                raise
            except Exception as e:
                last = str(e)
                time.sleep(6)
        if not loc:
            raise BrainError('提交模拟重试耗尽: %s' % last)

        for _ in range(poll):
            time.sleep(gap)
            try:
                j = self.s.get(loc, timeout=self.timeout).json()
            except Exception:
                continue
            s = j.get('status')
            if s == 'ERROR':
                raise BrainError('模拟报错: %s' % str(j.get('message'))[:300])
            if s and s not in ('PENDING', 'RUNNING', 'QUEUED'):
                aid = j.get('alpha')
                if not aid:
                    raise BrainError('模拟完成但没返回 alpha id')
                a = self.alpha(aid)
                if save_as:
                    fp = os.path.join(PROJ, 'data', 'alpha_quality_analysis', 'mined',
                                      save_as + '.json')
                    io.open(fp, 'w', encoding='utf-8').write(
                        json.dumps(a, ensure_ascii=False, indent=1))
                return a
        raise BrainError('模拟超时未完成 loc=%s' % loc)


def main():
    """自检：登录 + 拿一条 alpha 的检查项。"""
    b = Brain()
    say('登录成功')
    for aid in sys.argv[1:]:
        a = b.alpha(aid)
        isd = a.get('is') or {}
        say('%s status=%s S=%s F=%s T=%s' % (
            aid, a.get('status'), isd.get('sharpe'), isd.get('fitness'), isd.get('turnover')))
        m = b.check(aid)
        for k in ('SELF_CORRELATION', 'PROD_CORRELATION', 'OLD_SIMULATION', 'IS_LADDER_SHARPE'):
            if k in m:
                say('   %-22s %s / %s' % (k, m[k][0], m[k][1]))


if __name__ == '__main__':
    main()

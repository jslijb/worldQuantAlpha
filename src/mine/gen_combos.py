# -*- coding: utf-8 -*-
"""gen_combos.py —— 挖矿批次生成器统一驱动入口

用法：
    python src/mine/gen_combos.py w200 w203   # 跑指定批次
    python src/mine/gen_combos.py --all       # 跑全部批次
    python src/mine/gen_combos.py --list      # 列出可用批次
"""
import sys, pathlib as _pl
_src = _pl.Path(__file__).resolve().parent.parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from core import combo_gen as cg
import specs

# 批名 -> 生成函数：取 specs 里全部 build_ 前缀函数，批名 = 函数名去掉 build_ 前缀
BATCHES = {name[len('build_'):]: getattr(specs, name)
           for name in dir(specs) if name.startswith('build_') and callable(getattr(specs, name))}


def _norm(name):
    """批名规范化：去掉非字母数字字符（如 w213_B -> w213B 不匹配；w213b 原样）。"""
    return ''.join(ch for ch in name if ch.isalnum())


def main(argv):
    if '--list' in argv:
        print('可用批次（%d）：%s' % (len(BATCHES), ' '.join(sorted(BATCHES))))
        return 0
    if '--all' in argv:
        keys = sorted(BATCHES)
    else:
        keys = []
        for a in argv:
            k = _norm(a)
            if k not in BATCHES:
                print(f'未知批名 {a}！合法批名：{" ".join(sorted(BATCHES))}')
                return 1
            keys.append(k)
        if not keys:
            print('用法：python src/mine/gen_combos.py <批名...> | --all | --list')
            return 1
    for k in keys:
        comb = BATCHES[k]()
        print(f'批次 {k}：{len(comb)} 条组合')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

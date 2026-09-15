import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# ============================================================
# utils.py — WorldQuant Brain 公共工具模块
# 功能：提供所有脚本共享的基础函数
#   - sign_in()：登录 WorldQuant Brain API，返回已认证的 Session
#   - get_datafields()：分页获取指定数据集的所有数据字段，返回 DataFrame
# ============================================================
import requests
import json
import time
import pandas as pd
from os.path import expanduser
from requests.auth import HTTPBasicAuth


def sign_in():
    """登录 WorldQuant Brain API，返回已认证的 requests.Session 对象"""
    with open(expanduser('brain_credentials.txt')) as f:
        credentials = json.load(f)

    username, password = credentials

    sess = requests.Session()
    sess.auth = HTTPBasicAuth(username, password)

    response = sess.post('https://api.worldquantbrain.com/authentication')
    print(response.status_code)
    print(response.json())

    return sess


def get_datafields(s, searchScope, dataset_id='', search=''):
    """
    分页获取指定数据集的所有数据字段，返回 pandas DataFrame。

    Args:
        s: 已认证的 requests.Session
        searchScope: dict，包含 instrumentType, region, delay, universe
        dataset_id: 数据集 ID，如 'fundamental6'
        search: 可选的搜索关键词
    """
    instrument_type = searchScope['instrumentType']
    region = searchScope['region']
    delay = searchScope['delay']
    universe = searchScope['universe']

    if len(search) == 0:
        url_template = (
            "https://api.worldquantbrain.com/data-fields?"
            f"&instrumentType={instrument_type}"
            f"&region={region}&delay={str(delay)}&universe={universe}"
            f"&dataset.id={dataset_id}&limit=50"
            "&offset={x}"
        )
        first_resp = s.get(url_template.format(x=0)).json()
        count = first_resp.get('count', 0)
    else:
        url_template = (
            "https://api.worldquantbrain.com/data-fields?"
            f"&instrumentType={instrument_type}"
            f"&region={region}&delay={str(delay)}&universe={universe}"
            f"&limit=50&search={search}"
            "&offset={x}"
        )
        count = 100

    datafields_list = []
    for x in range(0, count, 50):
        for attempt in range(5):
            datafields = s.get(url_template.format(x=x))
            resp_json = datafields.json()
            if 'results' not in resp_json:
                msg = resp_json.get('message', '')
                if 'rate limit' in msg.lower():
                    wait = 10 * (attempt + 1)
                    print(f"  Rate limit hit at offset {x}, 等待 {wait}s 后重试 ({attempt+1}/5)...")
                    time.sleep(wait)
                    continue
                print(f"Warning: API response at offset {x} has no 'results' key: {resp_json}")
                break
            datafields_list.append(resp_json['results'])
            break
        time.sleep(1)  # 请求间隔，避免触发限流

    datafields_list_flat = [item for sublist in datafields_list for item in sublist]
    datafields_df = pd.DataFrame(datafields_list_flat)
    return datafields_df


def submit_and_confirm(sess, alpha_id, timeout=240, min_interval=1.0):
    """
    提交 Alpha 并执行强制三连确认（FR-7.1）。

    流程：
      1. POST /alphas/{id}/submit（200/201=接受，503=排队继续轮询，403=被拒）
      2. 轮询 GET /alphas/{id}/submit 直到 Retry-After=0
      3. 独立 GET /alphas/{id} 验证三字段全满足：
           status ∈ {ACTIVE, SUBMITTED}
           dateSubmitted 非空
           stage == "OS"

    Args:
        sess: 已认证 requests.Session
        alpha_id: Alpha ID
        timeout: 总轮询超时（秒），默认 240
        min_interval: 两次轮询最小间隔（秒），默认 1.0

    Returns:
        (success: bool, detail: dict)
        detail 含 status/dateSubmitted/stage/reason 等确认信息。
    """
    url = f'https://api.worldquantbrain.com/alphas/{alpha_id}/submit'
    detail = {'alpha': alpha_id}

    resp = sess.post(url)
    detail['post_status'] = resp.status_code
    if resp.status_code == 403:
        detail['success'] = False
        detail['reason'] = 'FORBIDDEN_CHECK_FAILED'
        try:
            body = resp.json()
            detail['body'] = body.get('is', {}).get('checks') or body
        except Exception:
            detail['body'] = resp.text[:300]
        return False, detail
    if resp.status_code not in (200, 201, 503):
        detail['success'] = False
        detail['reason'] = f'UNEXPECTED_STATUS_{resp.status_code}'
        return False, detail

    deadline = time.time() + timeout
    poll = None
    while time.time() < deadline:
        try:
            poll = sess.get(url)
        except Exception as exc:
            detail['poll_error'] = str(exc)
            time.sleep(min_interval)
            continue
        if poll.status_code == 403:
            detail['poll_status'] = 403
            detail['success'] = False
            detail['reason'] = 'SUBMISSION_REJECTED'
            try:
                body = poll.json()
                detail['body'] = body.get('is', {}).get('checks') or body
            except Exception:
                detail['body'] = poll.text[:300]
            return False, detail
        retry = float(poll.headers.get('Retry-After', 0) or 0)
        if retry == 0:
            break
        time.sleep(min(max(retry, min_interval), 10))
    else:
        detail['success'] = False
        detail['reason'] = 'POLL_TIMEOUT'
        return False, detail

    detail['poll_status'] = poll.status_code

    alpha = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}').json()
    status = alpha.get('status')
    date_submitted = alpha.get('dateSubmitted')
    stage = alpha.get('stage')
    detail['status'] = status
    detail['dateSubmitted'] = date_submitted
    detail['stage'] = stage

    success = (
        status in ('ACTIVE', 'SUBMITTED')
        and bool(date_submitted)
        and stage == 'OS'
    )
    detail['success'] = success
    if not success:
        detail['reason'] = 'CONFIRM_FIELDS_MISMATCH'
    return success, detail

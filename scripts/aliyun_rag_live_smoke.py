"""Explicit bounded activation smoke: one retrieval and at most two chats.

No credentials needed for the user-authorized public demo. No retries,
patients, experiment inputs, scientific scoring, or full corpus scans.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-model', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    base = 'http://8.148.158.242/zhiwei/api/agent/'
    rows = []

    def request(path, body=None):
        started = time.monotonic()
        headers = {'Origin':'http://8.148.158.242'}
        if body is not None:
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(base+path, headers=headers,
                  data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None,
                  method='POST' if body is not None else 'GET')
        try:
            response = opener.open(req,timeout=210)
        except urllib.error.HTTPError as error:
            response = error
        try:
            raw = response.read(2*1024*1024)
            try:
                data = json.loads(raw)
            except ValueError:
                data = {'non_json_body':True}
            row={'path':path,'http_status':response.status,'elapsed_seconds':round(time.monotonic()-started,2),
                 'request':body,'response':data}
            rows.append(row)
            summary={key:value for key,value in row.items() if key not in {'request','response'}}
            if isinstance(data,dict):
                summary.update(status=data.get('status'),can_chat=data.get('can_chat'),
                    model_invoked=data.get('model',{}).get('invoked'),
                    answer_mode=data.get('answer_mode'),evidence_supported=data.get('evidence_supported'),
                    answer_nonempty=bool(data.get('answer')),citation_count=len(data.get('citations',[])),
                    evidence_count=len(data.get('evidence_cards',[])),hits_count=len(data.get('hits',[])),
                    detail=data.get('detail'))
            print(json.dumps(summary,ensure_ascii=False),flush=True)
            return response.status,data
        finally:
            response.close()

    status, ready = request('status')
    success = status == 200 and ready.get('corpus',{}).get('ready') is True
    if success:
        status, result = request('evidence-search',{'query':'镉暴露与肾损伤', 'top_k':2,'candidate_k':8,'mode':'bm25'})
        success = status == 200 and len(result.get('hits',[])) > 0
    if args.allow_model and success and ready.get('can_chat') is True:
        for query in ['镉暴露与肾损伤', 'What does biomagnification mean? Explain briefly.']:
            status, result = request('chat',{'message':query,'history':[], 'enable_deep_think':False})
            passed = (status == 200 and bool(result.get('answer')) and
                      result.get('model',{}).get('invoked') is True)
            if query == '镉暴露与肾损伤':
                passed = passed and result.get('evidence_supported') is True and bool(result.get('citations'))
            success = success and passed
            if not passed:
                break
    elif args.allow_model:
        success = False
    receipt={'status':'PASS' if success else 'FAIL',
             'observed_at_utc':datetime.now(timezone.utc).isoformat(),
             'scope':'bounded activation smoke; not systematic quality, clinical validation or independent source appraisal',
             'model_requests':sum(row['path']=='chat' for row in rows),'checks':rows}
    # Generated test receipts are script output, not source-file edits.
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(receipt,stream,ensure_ascii=False,indent=2)
    print(json.dumps({'status':receipt['status'],'model_requests':receipt['model_requests']}),flush=True)
    return int(not success)


if __name__ == '__main__':
    raise SystemExit(main())

"""Bounded deployment smoke checks; no secrets or individual records printed."""
import argparse
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--private-env',type=Path)
    parser.add_argument('--demo-import',action='store_true')
    parser.add_argument('--public-demo',action='store_true', help='expect anonymous new-site API access')
    args=parser.parse_args()
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    base='http://127.0.0.1' if args.private_env else 'http://8.148.158.242'
    token=None
    if args.private_env:
        values=dict(line.split('=',1) for line in args.private_env.read_text().splitlines()
                    if line and not line.startswith('#'))
        token=values['RAG_API_KEY']
    def fetch(url,*,auth=False,method='GET',body=None):
        headers={'Origin':'http://8.148.158.242'}
        if auth:headers['Authorization']='Bearer '+token
        if body is not None:headers['Content-Type']='application/json'
        req=urllib.request.Request(url,headers=headers,method=method,
            data=json.dumps(body).encode() if body is not None else None)
        try:
            with opener.open(req,timeout=20) as r:
                return r.status,r.headers,r.read(2*1024*1024)
        except urllib.error.HTTPError as e:return e.code,e.headers,e.read(4096)
    fail=False
    for path in ['/', '/zhiwei/', '/zhiwei/datainput', '/zhiwei/data-cleaning']:
        status,headers,body=fetch(base+path)
        title=re.search(rb'<title>(.*?)</title>',body,re.S)
        print(json.dumps({'check':'page','path':path,'status':status,
            'content_type':headers.get('Content-Type'),
            'title':title.group(1).decode('utf-8','replace') if title else None},ensure_ascii=False))
        fail|=status!=200
        if path=='/zhiwei/' and status==200:
            text=body.decode('utf-8','replace')
            for asset in re.findall(r'(?:src|href)="(/zhiwei/_nuxt/[^"?]+)',text):
                a_status,a_headers,_=fetch(base+asset)
                print(json.dumps({'check':'asset','status':a_status,'content_type':a_headers.get('Content-Type')}))
                fail|=a_status!=200 or 'text/html' in a_headers.get('Content-Type','')
    for port in [3000,3001,8501]:
        url=('http://127.0.0.1' if args.private_env else 'http://8.148.158.242')+':'+str(port)
        status,_,body=fetch(url)
        title=re.search(rb'<title>(.*?)</title>',body,re.S)
        print(json.dumps({'check':'old_site','port':port,'status':status,
            'title':title.group(1).decode('utf-8','replace') if title else None},ensure_ascii=False))
        fail|=status!=200
    for path,expected in [('/zhiwei/api/info',200 if args.public_demo else 401),('/zhiwei/uploads/',404),('/zhiwei/docs',404)]:
        status,_,_=fetch(base+path)
        print(json.dumps({'check':'guard','path':path,'status':status,'expected':expected}))
        fail|=status!=expected
    if token or args.public_demo:
        for path in ['/zhiwei/api/info','/zhiwei/api/datainput/cleaning/schema','/zhiwei/api/datainput/demo','/zhiwei/api/agent/status']:
            status,_,body=fetch(base+path,auth=bool(token))
            result=json.loads(body) if status==200 else None
            row={'check':'authenticated_api' if token else 'anonymous_api','path':path,'status':status}
            if path.endswith('/agent/status') and result:
                row.update(generation_ready=result.get('model',{}).get('ready'),
                    configured_model=result.get('model',{}).get('name'),
                    corpus_ready=result.get('corpus',{}).get('ready'),
                    restore_receipt_required=result.get('corpus',{}).get('restore_receipt_required'),
                    restore_receipt_verified=result.get('corpus',{}).get('restore_receipt_verified'),
                    retrieval_mode=result.get('retrieval',{}).get('mode'))
            print(json.dumps(row,ensure_ascii=False))
            fail|=status!=200
        if args.demo_import:
            status,_,body=fetch(base+'/zhiwei/api/datainput/demo/import',auth=bool(token),method='POST')
            result=json.loads(body) if status==200 else None
            print(json.dumps({'check':'public_nhanes_demo_import','status':status,
                'result_keys':list(result) if isinstance(result,dict) else None,
                'success':result.get('success') if isinstance(result,dict) else None},ensure_ascii=False))
            fail|=status!=200
    print(json.dumps({'status':'FAIL' if fail else 'PASS','scope':'basic website/api/old-site smoke only; not clinical or systematic RAG validation'}))
    return int(fail)

if __name__=='__main__':raise SystemExit(main())

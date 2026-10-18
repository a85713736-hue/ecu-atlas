"""Run research from GitHub Actions or locally; SearXNG is optional."""
import argparse
import json
import os
import time
import urllib.request
import urllib.error
from researcher import run
from verify import verify
from extract import extract

def api(base, token, payload):
    url = base.rstrip('/') + '/api/agents/worker'
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={
        'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
        'User-Agent': 'ECUAtlasLocalWorker/0.1'}, method='POST')
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.load(response)

def once(base, token, searx):
    task = api(base, token, {'action':'claim'}).get('task')
    if not task:
        print('No queued research tasks', flush=True)
        return False
    print('Processing', task['id'], task['ecu'], flush=True)
    try:
        found = run(task['ecu'], searx)
        if all(not s['results'] for s in found['sections'].values()):
            raise RuntimeError('No search results. Verify SearXNG JSON search endpoint.')
        extracted = extract(found)
        review = verify(found)
        result = {'research':found,'extracted':extracted,'review':review}
        # Keep HTTP request bounded; the full output remains local as a backup.
        os.makedirs('research/out', exist_ok=True)
        with open('research/out/' + task['id'] + '.json','w',encoding='utf-8') as handle:
            json.dump(result,handle,ensure_ascii=False,indent=2)
        compact = {'review':{'source_count':review['source_count'],'review_status':'pending'},
                   'sources':review['findings'][:35], 'extracted_documents':extracted['documents'][:15],
                   'errors':review['errors'] + extracted['errors'][:10], 'publish_allowed':False}
        while len(json.dumps(compact,ensure_ascii=False))>220000 and compact['sources']:
            compact['sources'].pop()
        api(base,token,{'action':'complete','taskId':task['id'],'status':'completed','result':compact})
        print('Done; requires human review',flush=True)
    except Exception as exc:
        print('Research failed:',str(exc),flush=True)
        api(base,token,{'action':'complete','taskId':task['id'],'status':'failed','result':{'error':str(exc)[:600]}})
    return True

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--once',action='store_true')
    parser.add_argument('--interval',type=int,default=60)
    args=parser.parse_args()
    base=os.environ.get('ECU_ATLAS_URL','https://ecu-atlas-web.onrender.com')
    token=os.environ.get('AGENT_WORKER_TOKEN','')
    searx=os.environ.get('SEARXNG_URL','')
    if not token: raise SystemExit('Set AGENT_WORKER_TOKEN (not AGENT_ADMIN_TOKEN)')
    while True:
        try: once(base,token,searx)
        except (urllib.error.URLError,ValueError) as exc: print('Worker API error:',exc,flush=True)
        if args.once: break
        time.sleep(max(30,args.interval))
if __name__=='__main__':main()

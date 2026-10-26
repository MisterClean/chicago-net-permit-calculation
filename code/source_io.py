"""Small, logged, cacheable HTTP reader and deterministic data-file helpers."""
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
DERIVED = ROOT / 'data/derived'


def project_metadata(value):
    """Keep field definitions and freshness, omitting cached value samples."""
    return {k:value[k] for k in ['id','name','description','rowsUpdatedAt','createdAt'] if k in value} | {
        'columns':[{k:c[k] for k in ['fieldName','name','dataTypeName','description'] if k in c}
                   for c in value.get('columns',[]) if not c.get('fieldName','').startswith(':')]
    }


def url(domain, dataset, **params):
    return f'https://{domain}/resource/{dataset}.json?' + urllib.parse.urlencode(params)


def fetch(name, request_url, compressed=True, attempts=3):
    path = RAW / (name + ('.json.gz' if compressed else '.json'))
    receipt = RAW / (name + '.request.json')
    if path.exists() and receipt.exists():
        meta = json.loads(receipt.read_text())
        if meta['url'] != request_url:
            raise ValueError('Cached request differs: ' + name)
        return read(path)
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(request_url,headers={'User-Agent':'ChicagoHousingResearch/1.0','Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=180) as response:
                content = response.read()
                status = response.status
            parsed = json.loads(content)
            original_content=content
            if name.endswith('_schema'):
                parsed=project_metadata(parsed)
                content=json.dumps(parsed,ensure_ascii=False,indent=2).encode()
            stored = gzip.compress(content,mtime=0) if compressed else content
            path.write_bytes(stored)
            receipt.write_text(json.dumps({
                'url':request_url,'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                'http_status':status,'response_bytes':len(original_content),'stored_bytes':len(stored),
                'response_sha256':hashlib.sha256(original_content).hexdigest(),
                'stored_sha256':hashlib.sha256(stored).hexdigest(),
                'rows':len(parsed) if isinstance(parsed,list) else None,
                'projection':'field definitions and freshness only' if name.endswith('_schema') else None,
            },indent=2))
            print(name, len(parsed) if isinstance(parsed,list) else '-', 'rows;',len(stored),'stored bytes',flush=True)
            return parsed
        except Exception:
            if attempt == attempts-1: raise
            time.sleep(attempt+1)


def read(path):
    path = Path(path)
    payload = gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()
    return json.loads(payload)


def write_json(path, value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def write_csv(path, rows, fields=None):
    import csv
    rows=list(rows)
    fields=fields or list(rows[0]) if rows else fields or []
    with Path(path).open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})


def permit_records():
    result=[]
    for path in sorted(RAW.glob('permits_records_*.json.gz')):
        result.extend(read(path))
    return result

"""Execute these trusted analysis notebooks top-to-bottom and save outputs.

The standard-library executor runs project notebooks without requiring Jupyter.
No source notebooks are downloaded or executed.
The resulting nbformat-4 files also run normally in a Python Jupyter kernel.
"""
import base64
import contextlib
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import traceback
from source_io import ROOT,write_json


def markdown(text):
    out=[]
    for line in text.splitlines():
        escaped=html.escape(line)
        if line.startswith('#'):
            level=min(4,len(line)-len(line.lstrip('#')))
            out.append(f'<h{level}>'+escaped[level:].strip()+f'</h{level}>')
        elif line.strip():out.append('<p>'+escaped+'</p>')
    return '\n'.join(out)


def render(nb,path):
    blocks=[]
    for c in nb['cells']:
        source=''.join(c['source'])
        if c['cell_type']=='markdown':blocks.append(markdown(source));continue
        blocks.append('<details><summary>Code cell '+str(c['execution_count'])+'</summary><pre>'+html.escape(source)+'</pre></details>')
        for output in c['outputs']:
            if output['output_type']=='stream':blocks.append('<pre class="output">'+html.escape(output['text'])+'</pre>')
            elif 'image/png' in output.get('data',{}):blocks.append('<img alt="Executed analytical figure" src="data:image/png;base64,'+output['data']['image/png']+'">')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Executed analysis notebook</title><style>body{max-width:920px;margin:40px auto;padding:0 20px 60px;font:16px/1.65 system-ui;color:#202b34}h1{font-size:32px;line-height:1.25}h2{margin-top:42px;border-top:1px solid #d7dde2;padding-top:20px}h3{margin-top:32px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f6;padding:16px;font:12px/1.6 ui-monospace,monospace}details{margin:18px 0}summary{cursor:pointer;color:#31596f}img{max-width:100%;height:auto;display:block;margin:24px auto}p{margin:10px 0}</style><article>'''+''.join(blocks)+'</article></html>'
    path.write_text(page)


def main():
    os.chdir(ROOT);results=[]
    for path in sorted((ROOT/'notebooks').glob('*.ipynb')):
        nb=json.loads(path.read_text())
        assert nb['nbformat']==4 and nb['nbformat_minor']==5
        namespace={'__name__':'__main__'};count=0
        for c in nb['cells']:
            assert c['cell_type'] in ['markdown','code'] and isinstance(c['source'],list) and c.get('id')
            if c['cell_type']!='code':continue
            count+=1;c['execution_count']=count;c['outputs']=[]
            before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'report/figures').glob('*.png')} if (ROOT/'report/figures').exists() else {}
            buffer=io.StringIO()
            with contextlib.redirect_stdout(buffer),contextlib.redirect_stderr(buffer):
                exec(compile(''.join(c['source']),str(path)+':cell'+str(count),'exec'),namespace)
            if buffer.getvalue():c['outputs'].append({'output_type':'stream','name':'stdout','text':buffer.getvalue()})
            for figure in sorted((ROOT/'report/figures').glob('*.png')):
                # Save figures emitted by this cell even when their bytes match a
                # prior run. Cell source names the deterministic output filename.
                stem=figure.stem
                if stem in ''.join(c['source']):
                    c['outputs'].append({'output_type':'display_data','data':{'image/png':base64.b64encode(figure.read_bytes()).decode()},'metadata':{}})
        path.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+'\n')
        render(nb,path.with_suffix('.html'))
        results.append({'notebook':str(path.relative_to(ROOT)),'executed_code_cells':count,'status':'passed','executor':'included standard-library runner','html':str(path.with_suffix('.html').relative_to(ROOT))})
        print(path.name,count,'cells executed')
    write_json(ROOT/'data/derived/notebook_execution.json',results)


if __name__=='__main__':main()

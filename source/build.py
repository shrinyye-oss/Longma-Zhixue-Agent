"""Zero-dependency build: inline CSS, JS and demo cards into one offline HTML."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
source = ROOT / 'src' / 'index.template.html'
html = source.read_text(encoding='utf-8')
css = (ROOT/'src'/'style.css').read_text(encoding='utf-8')
js = (ROOT/'src'/'app.js').read_text(encoding='utf-8')
data = json.loads((ROOT/'data'/'knowledge.json').read_text(encoding='utf-8'))
assert len(data['topics']) == 10
assert sum(len(x['questions']) for x in data['topics']) >= 20
raw_data=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
html=html.replace('/* INJECT_CSS */',css).replace('/* INJECT_JS */',js).replace('/* INJECT_DATA */',raw_data)
assert '/* INJECT_' not in html
out=ROOT/'dist'/'龙马智学-离线可运行.html'
out.parent.mkdir(exist_ok=True)
out.write_text(html,encoding='utf-8')
print(f'Built {out}: {out.stat().st_size} bytes, {len(data["topics"])} chapters')

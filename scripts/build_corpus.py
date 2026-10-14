"""Import Vatican HTML, align all 1,752 canons, and build contextual Latin lemmas."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, re, requests, unicodedata
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache'
CACHE.mkdir(exist_ok=True)
BASE = 'https://www.vatican.va'
BOOKS = [(1,203,'General norms','De normis generalibus'),(204,746,'The people of God','De populo Dei'),(747,833,'The teaching office','De Ecclesiae munere docendi'),(834,1253,'The sanctifying office','De Ecclesiae munere sanctificandi'),(1254,1310,'Temporal goods','De bonis Ecclesiae temporalibus'),(1311,1399,'Penal sanctions','De sanctionibus poenalibus in Ecclesia'),(1400,1752,'Processes','De processibus')]
def fetch(url):
    file = CACHE / (hashlib.sha256(url.encode()).hexdigest()+'.html')
    if not file.exists():
        r=requests.get(url, timeout=60); r.raise_for_status(); file.write_bytes(r.content)
    return BeautifulSoup(file.read_bytes(),'html.parser')
def clean(text): return re.sub(r'\s+',' ',text).strip()
def parse(url):
    soup=fetch(url); result={}; current=None
    # Some source canons (English 1330) are bare table-cell content.
    if '/eng/' in url:
        for label in list(soup.find_all('b')):
            if re.match(r'^Can\.\s*\d+',label.get_text()) and not label.find_parent('p'):
                wrapper=soup.new_tag('p'); label.insert_before(wrapper)
                node=label
                while node is not None and getattr(node,'name',None) not in ['p','table']:
                    following=node.next_sibling; wrapper.append(node.extract()); node=following
    for br in soup.find_all('br'): br.replace_with(' ¶BREAK¶ ')
    for marker in soup.find_all(['sup','font']):
        if marker.get_text(strip=True)=='n': marker.decompose()
    special = [td for td in soup.find_all('td') if not td.find('td')] if url.endswith('cic_liberVI_la.html') else []
    for p in soup.find_all(['p','td']):
        if p.name=='td' and p not in special: continue
        if p.name=='p' and (p.find('p') or any(parent in special for parent in p.parents)): continue
        text=clean(p.get_text(' ',strip=True))
        text=re.sub(r'\[[^\]]+\]','',text).strip()
        text=re.sub(r'^(?:¶BREAK¶\s*)+','',text)
        if not text: continue
        # A few source paragraphs contain two consecutive canons (e.g. Latin 1666–1667).
        if not re.match(r'^(Can?\.|§|\d+[°º/.)])',text):
            prose=sum(c.islower() for c in text)>len(text)*0.4
            if current and prose and not p.find('a') and p.get('align')!='center' and not text.startswith(('\"','«','(','For Can.')):
                result[current]['paragraphs'].append(clean(text.replace('¶BREAK¶',' ')))
            else: current=None
            continue
        chunks=re.split(r'(?:¶BREAK¶\s*)+(?=Can?\.\s*\d+)|(?=Can\.\s*\d+\s*[—–-])',text)
        for text in chunks:
            text=clean(text.replace('¶BREAK¶',' '))
            if not text: continue
            m=re.match(r'^Can?\.\s*(\d+)\s*[.\-—–]?\s*', text, re.I)
            if m:
                current=int(m[1])
                if current in result:
                    current=None
                    continue
                result[current]={'paragraphs':[re.sub(r'^[ :—–-]+','',text[m.end():])],'source':url}
            elif current and (re.match(r'^(§|\d+[°º/.)])',text) or (text[0].islower() and not p.find('a'))):
                result[current]['paragraphs'].append(text)
            else: current=None
    return result
if __name__=='__main__':
    urls={}
    for lang,folder in [('la','latin'),('en','eng')]:
        index=fetch(f'{BASE}/archive/cod-iuris-canonici/cic_index_{lang}.html')
        urls[lang]=sorted(set(urldefrag(urljoin(BASE,a['href']))[0] for a in index.select('a[href]') if f'/{folder}/documents/cic_lib' in a['href'] and '.html' in a['href']))
    corpora={}
    for lang in urls:
        corpora[lang]={}
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            for result in pool.map(parse,urls[lang]):
                for n,value in result.items():
                    assert n not in corpora[lang],f'Duplicate {lang} {n}'
                    corpora[lang][n]=value
        missing=set(range(1,1753))-corpora[lang].keys()
        print(lang,len(corpora[lang]),'missing',sorted(missing),flush=True)
        assert not missing, f'Missing {lang} canons'
    canons=[]
    for n in range(1,1753):
        c={'n':n,'book':next(i+1 for i,b in enumerate(BOOKS) if b[0]<=n<=b[1])}
        for lang in ['la','en']:
            c[lang]='\n\n'.join(corpora[lang][n]['paragraphs'])
            c[lang+'Source']=corpora[lang][n]['source']
        translations=json.loads((ROOT/'scripts/english_supplements.json').read_text())
        if str(n) in translations:
            c['en']=translations[str(n)]
            c['enNote']='Study translation supplied for this reader because the Vatican English page includes amended text in Latin. Verify against the Latin source.'
        canons.append(c)
    (CACHE/'aligned.json').write_text(json.dumps(canons,ensure_ascii=False))
    import spacy
    nlp=spacy.load('la_core_web_sm',disable=['ner'])
    def norm(s):
        return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if not unicodedata.combining(c)).replace('j','i')
    overrides=json.loads((ROOT/'scripts/lemma_overrides.json').read_text())
    token_overrides=json.loads((ROOT/'scripts/token_overrides.json').read_text())
    for c,doc in zip(canons,nlp.pipe((c['la'] for c in canons),batch_size=32)):
        # LatinCy normalizes u/v and whitespace; remap tokens to untouched source text.
        source=norm(c['la']).replace('v','u'); cursor=0; c['tokens']=[]
        for t in doc:
            if t.is_space: continue
            surface=norm(t.text).replace('v','u')
            offset=source.find(surface,cursor)
            assert offset>=0, (c['n'],t.text,cursor)
            assert not any(x.isalpha() for x in source[cursor:offset]), (c['n'],'Skipped text',source[cursor:offset])
            cursor=offset+len(surface)
            if t.is_alpha:
                form=norm(c['la'][offset:cursor]); override=overrides.get(form)
                c['tokens'].append([offset,cursor,override[0] if override else norm(t.lemma_),override[1] if override else t.pos_,str(t.morph)])
        assert not any(x.isalpha() for x in source[cursor:]), (c['n'],'Unmapped tail')
        for correction in token_overrides.get(str(c['n']), []):
            matches=[t for t in c['tokens'] if c['la'][t[0]:t[1]]==correction['form'] and c['la'][t[1]:].startswith(correction['following'])]
            assert len(matches)==1, (c['n'],correction,len(matches))
            token=matches[0]
            token[2]=correction.get('lemma',token[2])
            token[3]=correction['pos']
        if c['n']%200==0: print('Lemmatized',c['n'],flush=True)
    data={'meta':{'title':'Code of Canon Law (1983)','retrieved':datetime.date.today().isoformat(),'edition':'Vatican website snapshot; individual language pages may incorporate amendments at different times. Not a certified consolidated edition.','model':'LatinCy la_core_web_sm '+nlp.meta['version']+' with lemma and token overrides','lemmaNote':'Contextual machine lemmatization. Inflections, including noun declensions and verb conjugations, are grouped by predicted dictionary headword. Predictions can be wrong, especially for ambiguous and ecclesiastical forms.','sources':urls},'books':[{'id':i+1,'start':b[0],'end':b[1],'en':b[2],'la':b[3]} for i,b in enumerate(BOOKS)],'canons':canons}
    out=ROOT/'dist/data/corpus.json'; out.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
    print('Saved',out,out.stat().st_size,flush=True)

import json,os,re,io,hashlib,requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36','Accept-Language':'ko-KR,ko;q=0.9,en;q=0.8'}
req=json.load(open('req.json'))
os.makedirs('out',exist_ok=True)
def img(u,ref,path,maxs=700):
    r=requests.get(u,headers={**UA,'Referer':ref},timeout=25); r.raise_for_status()
    im=Image.open(io.BytesIO(r.content)); 
    if im.width<180 or im.height<140: return None
    im=im.convert('RGBA'); bg=Image.new('RGB',im.size,'white'); bg.paste(im,mask=im.split()[3]); im=bg
    im.thumbnail((maxs,maxs)); im.save(path,'JPEG',quality=82); return [im.width,im.height]
for it in req.get('pages',[]):
    d=f"out/{it['id']}"; os.makedirs(d,exist_ok=True); log={'url':it['url']}
    try:
        r=requests.get(it['url'],headers=UA,timeout=30); r.encoding=r.apparent_encoding if not r.encoding or r.encoding.lower()=='iso-8859-1' else r.encoding
        html=r.text; log['status']=r.status_code
        if it.get('save'): open(d+'/page.html','w').write(html)
        s=BeautifulSoup(html,'html.parser')
        log['title']=(s.title.string or '').strip() if s.title else ''
        cands=[]
        for m in s.select('meta[property="og:image"],meta[name="twitter:image"]'):
            if m.get('content'): cands.append(m['content'])
        for t in s.find_all('img'):
            for a in ('data-original','data-src','ec-data-src','src'):
                v=t.get(a)
                if v and not v.startswith('data:'): cands.append(v); break
        seen=[];
        for c in cands:
            c=urljoin(it['url'],c.strip())
            if c not in seen and not re.search(r'\.(gif|svg)(\?|$)',c,re.I): seen.append(c)
        log['imgs']=[]
        for c in seen[:it.get('n',14)]:
            try:
                p=f"{d}/{len(log['imgs']):02d}.jpg"; wh=img(c,it['url'],p)
                if wh: log['imgs'].append([p,c,wh])
            except Exception as e: pass
    except Exception as e: log['err']=str(e)
    json.dump(log,open(d+'/log.json','w'),ensure_ascii=False,indent=1)
for it in req.get('images',[]):
    os.makedirs('out/img',exist_ok=True)
    try: wh=img(it['url'],it.get('ref',it['url']),f"out/img/{it['id']}.jpg"); print(it['id'],wh)
    except Exception as e: print(it['id'],'ERR',e)

"""한글 ISO 전수 검사: 텍스트 자원에서 영어로 남은 문장 수집 -> work/audit.json"""
import sys, os, re, json, io
sys.path.insert(0,os.path.dirname(__file__))
import pycdlib, hog, mrk, strdat, gui
iso=pycdlib.PyCdlib(); iso.open(sys.argv[1])
def eng(t):
    if isinstance(t,bytes):
        if any(c>=0x80 and c not in (0x87,0x8a,0xd1) for c in t): return False
        t=t.decode('latin-1')
    w=re.findall(r'[A-Za-z]{3,}',t)
    return len(w)>=1
out={'MRK':{},'STR':{},'GUI':{},'SUB':{}}
def add(cat,t,where):
    s=t.decode('latin-1') if isinstance(t,bytes) else t
    out[cat].setdefault(s,where)
def walk(d,path):
    try: items,_=hog.read(d)
    except Exception: return
    for n,b in items:
        p=path+'/'+n
        if b[:4]==b'HGZ\0' or hog.is_hog(b): walk(b,p)
        elif b[:4]==b'SMRK':
            for t in mrk.parse(b):
                if eng(t): add('MRK',t,p)
        elif n.upper() in ('STRINGS.DAT','STRINGS_E.DAT') and len(b)>4:
            for k,t in strdat.parse(b):
                if eng(t): add('STR',t,p+':'+k)
        elif n.upper().endswith('.GUI') and b[:3]==b'GUI':
            for t0,txt,*_ in gui.extract(b):
                if not txt.startswith(b'$') and eng(txt): add('GUI',txt,p)
for root,dirs,files in iso.walk(iso_path='/PSP_GAME/USRDIR'):
    for f in files:
        fn=f.split(';')[0]; ip=root.rstrip('/')+'/'+f
        if not fn.upper().endswith(('.HGZ','.HOG','.SUB')): continue
        bio=io.BytesIO(); iso.get_file_from_iso_fp(bio,iso_path=ip); d=bio.getvalue()
        if fn.upper().endswith('.SUB'):
            for m in re.finditer(rb'(?m)^\s*"([^"\r\n]*)"?\s*$',d):
                if eng(m.group(1)): add('SUB',m.group(1),fn)
        else: walk(d,ip)
print({k:len(v) for k,v in out.items()})
json.dump(out,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=0)

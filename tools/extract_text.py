"""원문 추출 -> work/src/all.json : [{en, src, key}] (영어 원문 고유)
대상: COMMON STRINGS.DAT/STRINGS_E.DAT(루즈+컨테이너), 레벨 STRINGS.DAT, *.MRK, *.GUI, 루즈 *.SUB(영어 FEED)"""
import sys, re, glob, json, os
sys.path.insert(0, os.path.dirname(__file__))
import hog, gui, strdat, mrk
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); I = R+'/work/iso/PSP_GAME/USRDIR/'
out = {}
def add(t, src, key=''):
    if isinstance(t, bytes): t = t.decode('utf-8', 'replace')
    if not re.search('[A-Za-z]{2}', t): return
    if t not in out: out[t] = dict(en=t, src=src, key=key)
def walk(b, p):
    it, _ = hog.read(b)
    for n, x in it:
        u = n.upper()
        if u.endswith('.GUI'):
            for t0, txt, font, cls, name in gui.extract(x):
                if not txt.startswith(b'$'): add(txt, 'gui')
        elif u in ('STRINGS.DAT', 'STRINGS_E.DAT'):
            for k, v in strdat.parse(x): add(v, 'str', k)
        elif u.endswith('.MRK') and x[:4] == b'SMRK':
            for t in mrk.parse(x): add(t, 'mrk:'+u)
        if hog.isgz(x) or hog.is_hog(x): walk(x, p+'/'+n)
for f in ['STRINGS.DAT', 'STRINGS_E.DAT']:
    for k, v in strdat.read(I+'GAMEDATA/COMMON/'+f): add(v, 'str', k)
for f in sorted(glob.glob(I+'GAMEDATA/**/*.H[OG][GZ]', recursive=True)): walk(open(f, 'rb').read(), f)
def sub_lines(t):
    a = t.index('%FEED ENGLISH'); b = t.find('%FEED', a+5); t = t[a:b if b > 0 else None]
    return re.findall(r'(?m)^\s*"([^"\r\n]*)"?\s*$', t)
for f in sorted(glob.glob(I+'*.SUB')):
    for l in sub_lines(open(f, 'rb').read().decode('utf-8-sig')): add(l, 'sub')
L = list(out.values())
json.dump(L, open(R+'/work/src/all.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
import collections
c = collections.Counter(e['src'].split(':')[0] for e in L); print(len(L), c, sum(len(e['en']) for e in L))

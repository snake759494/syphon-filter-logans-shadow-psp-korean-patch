"""LS_PVP.DAT 텍스트 추출 -> work/src/pvp.json [{en,src}] (trans/ko.json 에 없는 것만)"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
import hog, gui, strdat, mrk, pvpdat
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
T = json.load(open(R + '/trans/ko.json', encoding='utf-8'))
out = {}
def add(t, src):
    if isinstance(t, bytes): t = t.decode('utf-8', 'replace')
    if not re.search('[A-Za-z]{2}', t) or t in T: return
    out.setdefault(t, dict(en=t, src=src))
def member(n, x, p):
    u = n.upper()
    if u.endswith('.GUI') and x[:3] == b'GUI':
        for t0, txt, *_ in gui.extract(x):
            if not txt.startswith(b'$'): add(txt, 'gui')
    elif u.endswith('STRINGS.DAT') and len(x) > 4:
        try: it = strdat.parse(x)
        except Exception: it = []
        for k, v in it: add(v, 'str')
    elif u.endswith('.MRK') and x[:4] == b'SMRK':
        for t in mrk.parse(x): add(t, 'mrk:' + u)
    elif hog.isgz(x) or hog.is_hog(x):
        for n2, x2 in hog.read(x)[0]: member(n2, x2, p + '/' + n2)
d = open(R + '/work/iso/PSP_GAME/USRDIR/' + (sys.argv[1] if len(sys.argv) > 1 else 'LS_PVP/LS_PVP.DAT'), 'rb').read()
for e in pvpdat.entries(d): member(e['name'], pvpdat.get(d, e), e['name'])
L = list(out.values()); json.dump(L, open(R + '/work/src/' + (sys.argv[2] if len(sys.argv) > 2 else 'pvp.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
import collections
print(len(L), collections.Counter(e['src'].split(':')[0] for e in L), sum(len(e['en']) for e in L))

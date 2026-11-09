"""전체 빌드: 원본 ISO -> 한글 ISO
trans/ko.json : {영어 원문: 번역}  (STRINGS·MRK·GUI·SUB 공통)
trans/mrk_short.json : {영어 원문: 줄인 번역} (MRK 슬롯 초과 시)
trans/meta.json : {"title": ...}"""
import sys, os, json, glob, re, struct
sys.path.insert(0, os.path.dirname(__file__))
import hog, kfont, kenc, strdat, isobuild, gui, mrk, prx_patch, pvpdat
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
W = os.path.join(ROOT, 'work'); X = os.path.join(W, 'iso')
ORIG = os.path.join(ROOT, "Syphon Filter - Logan's Shadow (USA).iso")
OUT = os.path.join(ROOT, "Syphon Filter - Logan's Shadow (Korean).iso")
U = 'PSP_GAME/USRDIR/'; G = U+'GAMEDATA/'
def rd(p): return open(os.path.join(X, p), 'rb').read()
def lj(n, d=None):
    p = os.path.join(ROOT, 'trans', n)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else (d if d is not None else {})

def kfont_hog(it, chars, full=('DEFAULT',)):
    """글꼴 묶음 {name: bytes} -> full 글꼴에는 한글 글리프 레코드(같은 KDEF_* 페이지 공유),
    나머지 글꼴은 페이지 이름만 붙임(LS.PRX 패치: 자기 표가 없으면 G 에서 조회).
    묶음이 약 240KB 를 넘으면 실행 중 힙이 깨짐 -> full 은 크기 한도 안에서만."""
    nw = dict(it); names = [n for n in ('DEFAULT', 'CALLOUT', 'TINYFNT', 'LARGEFNT') if n+'.FNT' in it]
    fo, pg = kfont.build_shared({n: it[n+'.FNT'] for n in names if n in full}, chars, 'DEFAULT', 'KDEF')
    nw.update(pg)
    for n in names:
        if n in full: nw[n+'.FNT'] = fo[n]; continue
        f = kfont.read(it[n+'.FNT']); f['pages'] += sorted(pg)
        if n != 'LARGEFNT': f['hdr'][0] = max(f['hdr'][0], 14)   # 한글(12px) 줄 겹침 방지
        nw[n+'.FNT'] = kfont.write(f)
    assert len(hog.build(sorted(nw.items()))) <= 240000, len(hog.build(sorted(nw.items())))
    return nw

def main(only=None):
    T = {k: v for k, v in lj('ko.json').items() if v}
    SH = lj('mrk_short.json'); meta = lj('meta.json'); PS = lj('prx_str.json')
    chars = kenc.needed_chars(list(T.values()) + list(SH.values()) + list(PS.values()) + [meta.get('title', '')])
    E = kenc.Enc(chars); print('음절 수', len(chars))
    def tr(b):
        s = b.decode('utf-8', 'replace')
        return E.enc(T[s]) if s in T else None
    files = {}
    # 글꼴
    kfont.TEMPLATE = None
    for n, x in hog.read(rd(G+'FRONTEND/UI_GROUPS/SHELL_UNFREED.HGZ'))[0]:
        if n == 'GREEN_GABELIAN.TDX': kfont.TEMPLATE = x
    items, raw = hog.read(rd(G+'COMMON/FONTS_PSP.HOG')); d = dict(items); new = dict(items)
    # 한글 글리프 레코드는 DEFAULT 에만(크기 한도), 나머지는 G 경유
    new = kfont_hog(d, chars)
    prx = bytearray(prx_patch.patch(rd(U+'LS.PRX')))
    for en, ko in PS.items():   # 실행파일 내장 문자열(제자리 교체, 길이 이하)
        a = bytes(prx).index(en.encode() + bytes(1)); kb = E.enc(ko)
        assert len(kb) <= len(en), (en, len(kb)); prx[a:a+len(en)] = kb + bytes(len(en) - len(kb))
    files[U+'LS.PRX'] = bytes(prx)
    import hashlib
    TEX = {os.path.basename(f)[:-4]: open(f, 'rb').read() for f in glob.glob(os.path.join(ROOT, 'trans', 'tex', '*.tdx'))}
    fh = hog.build(sorted(new.items())); fz = hog.hgz(fh, magic=b'HZ2\0')
    print('FONTS', len(fh))
    stat = dict(tex=0, str=0, strmiss=0, mrk=0, mrkcut=[], gui=0)
    def do_str(b):
        try: it = strdat.parse(b)
        except Exception: return None
        out = []; ch = False
        for k, v in it:
            n = tr(v)
            if n is not None: out.append((k, n)); ch = True; stat['str'] += 1
            else:
                out.append((k, v))
                if re.search(rb'[A-Za-z]{2}', v): stat['strmiss'] += 1
        return strdat.dump(out) if ch else None
    def member(mp, n, b):
        u = n.upper()
        if u in ('FONTS.HGZ', 'FONTS2.HGZ'): return fz
        if u == 'FONTS_PSP.HOG': return fh
        if u in ('STRINGS.DAT', 'STRINGS_E.DAT') and len(b) > 4: return do_str(b)
        if u.endswith('.TDX'):
            h = hashlib.md5(b).hexdigest()
            if h in TEX: stat['tex'] += 1; return TEX[h]
            return None
        if u.endswith('.MRK') and b[:4] == b'SMRK':
            ts = mrk.parse(b); cp = mrk.caps(b); nt = []
            for t, c in zip(ts, cp):
                s = t.decode('utf-8', 'replace'); e = E.enc(T[s]) if s in T else t
                if len(e) > c and s in SH: e = E.enc(SH[s])
                if len(e) > c: stat['mrkcut'].append(s); e = t
                elif e != t: stat['mrk'] += 1
                nt.append(e)
            return mrk.build_fixed(b, nt) if nt != ts else None
        if u.endswith('.GUI') and b[:3] == b'GUI':
            m = {}
            for t0, txt, *_ in gui.extract(b):
                n2 = tr(txt)
                if n2 is not None: m[t0] = n2
            if m: stat['gui'] += len(m); return gui.replace(b, m)
        return None
    files[G+'COMMON/FONTS_PSP.HOG'] = fh
    # 별도 글꼴 묶음 FONTS_RP(스토리 레벨에서는 FONTS.HGZ 가 내려가고 이것만 남음)
    for fn in ('FONTS_RP.HGZ',):   # FONTS_PS2.HOG 는 FNT v4.0(PS2용), PSP에서 미사용
        o = rd(G+'COMMON/'+fn); b = hog.build(sorted(kfont_hog(dict(hog.read(o)[0]), chars, ('DEFAULT', 'CALLOUT', 'TINYFNT')).items()))
        files[G+'COMMON/'+fn] = hog.hgz(b, magic=o[:4]) if hog.isgz(o) else b
    files[G+'COMMON/FONTS.HGZ'] = fz; files[G+'COMMON/FONTS2.HGZ'] = fz
    for f in ('STRINGS.DAT', 'STRINGS_E.DAT'):
        r = do_str(rd(G+'COMMON/'+f))
        if r: files[G+'COMMON/'+f] = r
    for p in sorted(glob.glob(os.path.join(X, G, '**', '*.H[OG][GZ]'), recursive=True)):
        rel = os.path.relpath(p, X).replace(os.sep, '/')
        if rel in files: continue
        o = open(p, 'rb').read()
        if not (hog.isgz(o) or hog.is_hog(o)): continue
        nb = hog.repack(o, member)
        if nb is not o: files[rel] = nb
    # 멀티플레이(LS_PVP)·Combat Ops 데모: 별도 PRX + 가상 파일시스템 DAT, 같은 엔진 형식
    for PV, DN in ((U+'LS_PVP/', 'LS_PVP'), (U+'COMBAT_OPS/', 'COMBAT_OPS_DEMO')):
        pd = rd(PV+DN+'.DAT'); PE = {e['name']: e for e in pvpdat.entries(pd)}
        FN = next(n for n, e in PE.items() if pvpdat.get(pd, e)[:3] in (b'HZ2', b'HOG') and b'DEFAULT.FNT' in hog.hgz_names(pvpdat.get(pd, e)))
        pnew = kfont_hog(dict(hog.read(pvpdat.get(pd, PE[FN]))[0]), chars)
        prep = {FN: hog.hgz(hog.build(sorted(pnew.items())), magic=b'HZ2\0')}
        for nm, e in PE.items():
            if nm in prep: continue
            o = pvpdat.get(pd, e)
            if hog.isgz(o) or hog.is_hog(o):
                nb = hog.repack(o, member)
                if nb is not o: prep[nm] = nb
            else:
                nb = member(None, nm.split('/')[-1], o)
                if nb is not None: prep[nm] = nb
        files[PV+DN+'.DAT'] = pvpdat.replace(pd, prep)
        files[PV+DN+'.PRX'] = prx_patch.patch(rd(PV+DN+'.PRX'))
        print(DN, '교체 파일', len(prep))
    # SUB (영어 FEED 줄 교체)
    for p in sorted(glob.glob(os.path.join(X, U, '*.SUB'))):
        t = open(p, 'rb').read(); s = t.decode('utf-8-sig'); bom = t[:3] == b'\xef\xbb\xbf'
        a = s.index('%FEED ENGLISH'); bnd = s.find('%FEED', a+5); bnd = len(s) if bnd < 0 else bnd
        def rp(m):
            k = m.group(2)
            return m.group(1)+'"'+(E.enc(T[k]).decode('utf-8') if k in T else k)+'"'+m.group(3)
        seg = re.sub(r'(?m)^([ \t]*)"([^"\r\n]*)"?([ \t]*\r?)$', rp, s[a:bnd])   # CRLF 파일
        ns = s[:a]+seg+s[bnd:]
        files[U+os.path.basename(p)] = (b'\xef\xbb\xbf' if bom else b'')+ns.encode('utf-8')
    # PARAM.SFO / ICON
    sfo = bytearray(rd('PSP_GAME/PARAM.SFO')); ttl = meta.get('title')
    if ttl:
        tb = ttl.encode('utf-8')+b'\0'
        ko, do = struct.unpack_from('<II', sfo, 8); n = struct.unpack_from('<I', sfo, 16)[0]
        for i in range(n):
            kof, fmt, ln, mx, dof = struct.unpack_from('<HHIII', sfo, 20+16*i)
            if sfo[ko+kof:ko+kof+6] == b'TITLE\0':
                assert len(tb) <= mx
                sfo[do+dof:do+dof+mx] = tb+bytes(mx-len(tb)); struct.pack_into('<I', sfo, 20+16*i+4, len(tb))
        files['PSP_GAME/PARAM.SFO'] = bytes(sfo)
    print('TEX', stat['tex'], 'STR', stat['str'], '미번역', stat['strmiss'], 'MRK', stat['mrk'], '잘림', len(set(stat['mrkcut'])), 'GUI', stat['gui'], '파일', len(files))
    json.dump(sorted(set(stat['mrkcut'])), open(os.path.join(W, 'mrk_over.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    if os.path.exists(OUT): os.remove(OUT)
    iso = isobuild.Iso(ORIG, OUT)
    for p, b in files.items():
        if only and not any(o in p for o in only): continue
        iso.replace(p, b)
    iso.close(); print('완료', OUT)
if __name__ == '__main__': main(sys.argv[1:] or None)

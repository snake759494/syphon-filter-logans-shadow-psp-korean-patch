"""로간스 섀도우 FNT v4 + 한글 글리프 페이지 생성
FNT v4: 04 01, u32 npages, (u8 len,name)*, 5*u32 hdr(lineh,base,?,spacew,?), u32 n, n*8 glyph(page,x,y,w,h,xoff s8,yoff u8,adv s8), n*u32 codepoint, tail(12B)
한글 음절 k -> 코드포인트 0x100+k (UTF-8 2바이트)"""
import struct, os, sys
from PIL import Image, ImageFont, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import tdx
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TTF = os.path.join(ROOT, 'work', 'fonts', 'ttf')
BASE_CP = 0x180   # 원본 글꼴 코드(œ 0x153 등)와 겹치지 않게; 0x7FF까지 1664자
PAGE = int(os.environ.get('KPAGE','256'))

def read(d):
    o = 2; np_ = struct.unpack_from('<I', d, o)[0]; o += 4; pages = []
    for i in range(np_):
        l = d[o]; pages.append(d[o+1:o+1+l].decode()); o += 1+l
    hdr = list(struct.unpack_from('<5I', d, o)); o += 20
    n = struct.unpack_from('<I', d, o)[0]; o += 4
    gl = [list(struct.unpack_from('<BBBBBbBb', d, o+8*i)) for i in range(n)]; o += 8*n
    cps = list(struct.unpack_from('<%dI' % n, d, o)); o += 4*n
    return dict(ver=d[:2], pages=pages, hdr=hdr, glyphs=gl, cps=cps, tail=d[o:])

def write(f):
    b = bytearray(f['ver']) + struct.pack('<I', len(f['pages']))
    for p in f['pages']: b += bytes([len(p)]) + p.encode()
    b += struct.pack('<5I', *f['hdr']) + struct.pack('<I', len(f['glyphs']))
    for g in f['glyphs']: b += struct.pack('<BBBBBbBb', *g)
    b += struct.pack('<%dI' % len(f['cps']), *f['cps'])
    b += f['tail']; return bytes(b)

CFG = {
 'DEFAULT':  dict(ttf='Galmuri11.ttf', size=12, aa=False, lineh=14, adv_extra=0),
 'CALLOUT':  dict(ttf='Galmuri11.ttf', size=12, aa=False, lineh=13, adv_extra=0),
 'TINYFNT':  dict(ttf='Galmuri9.ttf', size=10, aa=False, adv_extra=0),
 'LARGEFNT': dict(ttf=os.path.join(ROOT, 'NanumSquareNeo-eHv.ttf'), size=18, aa=True, adv_extra=1),
}

def render(ch, c, ft):
    asc, desc = ft.getmetrics()
    S = c['size']*3
    im = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(im)
    if not c['aa']: dr.fontmode = '1'
    ox = oy = c['size']
    dr.text((ox, oy), ch, font=ft, fill=255)
    adv = int(round(ft.getlength(ch))) + c['adv_extra']
    bb = im.getbbox()
    if bb is None: return None, 0, 0, adv
    return im.crop(bb), bb[0]-ox, (oy+asc)-bb[1], adv

TEMPLATE = None   # 256x256 4bpp TDX (헤더 0x60 + 팔레트 16)
def make_tdx(img):
    h = bytearray(TEMPLATE[:0xa0]); h[2] = 0x07
    struct.pack_into('<HH', h, 4, PAGE, PAGE); struct.pack_into('<I', h, 0xc, ((PAGE*PAGE//2) << 16) & 0xffffffff)
    for i in range(16):
        v = i*17; h[0x60+4*i:0x64+4*i] = bytes([v, v, v, v])
    px = img.getdata(); raw = bytearray(PAGE*PAGE//2)
    for i in range(0, PAGE*PAGE, 2):
        a = (px[i]*15+127)//255; b = (px[i+1]*15+127)//255
        raw[i//2] = a | (b << 4)
    return bytes(h) + tdx.swizzle(bytes(raw), PAGE//2, PAGE)

def build(name, orig_fnt, chars):
    assert BASE_CP+len(chars) <= 0x800, len(chars)
    """chars: 한글 음절 리스트 (k번째 -> 0x100+k). returns (fnt bytes, {page: tdx})"""
    c = CFG[name]; f = read(orig_fnt)
    ttf = c['ttf'] if os.path.isabs(c['ttf']) else os.path.join(TTF, c['ttf'])
    ft = ImageFont.truetype(ttf, c['size'])
    if 'lineh' in c: f['hdr'][0] = max(f['hdr'][0], c['lineh'])
    base = f['hdr'][1]
    # 원본 대문자 높이에 맞춰 세로 위치 정렬: 한글 윗변을 대문자 윗변(yoff of 'H') 근처로
    gi = {cp: g for cp, g in zip(f['cps'], f['glyphs'])}
    capH = gi[ord('H')][6] if ord('H') in gi else base
    pages = []; cur = None; x = y = rowh = 0
    def newpage():
        nonlocal cur, x, y, rowh
        cur = Image.new('L', (PAGE, PAGE), 0); pages.append(cur); x = y = rowh = 0
    newpage()
    p0 = len(f['pages'])
    for k, ch in enumerate(chars):
        g, xoff, yoff, adv = render(ch, c, ft)
        cp = BASE_CP + k
        if g is None:
            f['glyphs'].append([0, 0, 0, 0, 0, 0, 0, adv]); f['cps'].append(cp); continue
        w, h = g.size; pw, ph = w+2, h+2
        if x+pw > PAGE: x = 0; y += rowh; rowh = 0
        if y+ph > PAGE: newpage()
        cur.paste(g, (x+1, y+1))
        f['glyphs'].append([p0+len(pages)-1, x, y, pw, ph, xoff-1, yoff+1+c.get('dy',0), adv])
        f['cps'].append(cp)
        x += pw; rowh = max(rowh, ph)
    names = ['%s_%d.TDX' % (name, i+p0) for i in range(len(pages))]
    f['pages'] += names
    # 코드포인트 정렬(이진 탐색 대비)
    order = sorted(range(len(f['cps'])), key=lambda i: f['cps'][i])
    f['glyphs'] = [f['glyphs'][i] for i in order]; f['cps'] = [f['cps'][i] for i in order]
    return write(f), {n: make_tdx(p) for n, p in zip(names, pages)}

def build_shared(fnts, chars, cfg, prefix):
    """fnts: {name: orig fnt bytes}; 같은 글리프 페이지(prefix_n.TDX)를 여러 FNT가 공유.
    returns ({name: fnt bytes}, {page: tdx})"""
    c = CFG[cfg]
    ttf = c['ttf'] if os.path.isabs(c['ttf']) else os.path.join(TTF, c['ttf'])
    ft = ImageFont.truetype(ttf, c['size'])
    pages = []; cur = None; x = y = rowh = 0; recs = []
    def newpage():
        nonlocal cur, x, y, rowh
        cur = Image.new('L', (PAGE, PAGE), 0); pages.append(cur); x = y = rowh = 0
    newpage()
    for k, ch in enumerate(chars):
        g, xoff, yoff, adv = render(ch, c, ft)
        if g is None: recs.append((None, 0, 0, 0, 0, 0, 0, adv)); continue
        w, h = g.size; pw, ph = w+2, h+2
        if x+pw > PAGE: x = 0; y += rowh; rowh = 0
        if y+ph > PAGE: newpage()
        cur.paste(g, (x+1, y+1))
        recs.append((len(pages)-1, x, y, pw, ph, xoff-1, yoff+1+c.get('dy', 0), adv))
        x += pw; rowh = max(rowh, ph)
    names = ['%s_%d.TDX' % (prefix, i) for i in range(len(pages))]
    out = {}
    for nm, ob in fnts.items():
        f = read(ob); p0 = len(f['pages'])
        if 'lineh' in c: f['hdr'][0] = max(f['hdr'][0], c['lineh'])
        f['pages'] += names
        for k, r in enumerate(recs):
            pg = 0 if r[0] is None else p0+r[0]
            f['glyphs'].append([pg]+list(r[1:])); f['cps'].append(BASE_CP+k)
        out[nm] = write(f)
    return out, {n: make_tdx(p) for n, p in zip(names, pages)}

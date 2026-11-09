"""영어 글자 텍스처 -> 한글 재작성. 결과: trans/tex/<원본md5>.tdx (build.py 가 이름 무관하게 md5로 교체)
대상: 상호작용 아이콘(CODE/CARD/i-SCAN), 임시 임무 썸네일(PLACEHOLDER ...), SCE 'presents' 문구"""
import sys, os, glob, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import tdx, hog
from PIL import Image, ImageDraw, ImageFont
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TTF = os.path.join(R, 'work', 'fonts', 'ttf')
OUT = os.path.join(R, 'trans', 'tex')
def F(n, s): return ImageFont.truetype(os.path.join(TTF, n) if n.startswith('Galmuri') else os.path.join(R, n), s)

def put(im, txt, ft, cx, cy, fill, spacing=2):
    d = ImageDraw.Draw(im); b = d.multiline_textbbox((0, 0), txt, font=ft, spacing=spacing, align='center')
    d.multiline_text((cx - (b[0] + b[2]) // 2, cy - (b[1] + b[3]) // 2), txt, font=ft, fill=fill, spacing=spacing, align='center')

def bbox(im, pred, x0=0, x1=None, y0=0, y1=None):
    w, h = im.size; px = im.load(); x1 = x1 or w; y1 = y1 or h
    pts = [(x, y) for y in range(y0, y1) for x in range(x0, x1) if pred(px[x, y])]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)

white = lambda c: c[0] > 150 and c[1] > 150 and c[2] > 150 and c[3] > 100

def icon(im, txt, xlim=None):
    x0, y0, x1, y1 = bbox(im, white, 0, xlim, 4)
    d = ImageDraw.Draw(im); d.rectangle((x0 - 1, y0 - 1, x1 + 1, y1 + 1), fill=(0, 0, 0, 255))
    put(im, txt, F('Galmuri11-Bold.ttf', 12), (x0 + x1) // 2 + 1, (y0 + y1) // 2 + 1, (255, 255, 255, 255))
    return im

def mission(im, txt, red=False):
    pred = (lambda c: c[0] > 150 and c[1] < 80) if red else white
    x0, y0, x1, y1 = bbox(im, pred, 8, 120, 4, 44)
    px = im.load(); bg = (0, 0, 0, 255) if red else px[x0 - 3, (y0 + y1) // 2]
    d = ImageDraw.Draw(im); d.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), fill=bg)
    put(im, txt, F('Galmuri11-Bold.ttf', 12), 64, (y0 + y1) // 2 + 1, (255, 40, 40, 255) if red else (235, 240, 245, 255))
    return im

def presents(im):
    d = ImageDraw.Draw(im); d.rectangle((0, 0, im.width, im.height), fill=(0, 0, 0, 255))
    put(im, '소니 컴퓨터 엔터테인먼트', F('NanumSquareNeo-bRg.ttf', 24), 256, 22, (255, 255, 255, 255))
    put(im, '제공', F('NanumSquareNeo-bRg.ttf', 14), 256, 50, (255, 255, 255, 255))
    return im

JOBS = {
    'CODE.TDX': lambda im: icon(im, '암호'),
    'ISCAN.TDX': lambda im: icon(im, '스캔'),
    'CARD.TDX': lambda im: icon(im, '카드', 50),
    'PRESENTS_TEXT.TDX': presents,
    'MISSION_TEST_A4.TDX': lambda im: mission(im, '준비 중', True),
    'MISSION_CANAL_B1.TDX': lambda im: mission(im, '준비 중\n운하 B1'),
    'MISSION_PRISN_D1.TDX': lambda im: mission(im, '준비 중\n교도소 D1'),
}
for i, c in enumerate('ABCDE'):
    JOBS['MISSION_BONUS_%s1.TDX' % c] = (lambda n: lambda im: mission(im, '준비 중\n보너스 %d' % n))(i + 1)

def main(show=None):
    os.makedirs(OUT, exist_ok=True); done = {}
    def walk(b):
        for n, x in hog.read(b)[0]:
            u = n.upper()
            if u in JOBS:
                h = hashlib.md5(x).hexdigest()
                if h not in done:
                    im = JOBS[u](tdx.decode(x, True)[0].convert('RGBA'))
                    nb = tdx.encode_like(x, im, True); assert len(nb) == len(x)
                    open(os.path.join(OUT, h + '.tdx'), 'wb').write(nb); done[h] = u
                    if show: tdx.decode(nb, True)[0].resize((im.width * 3, im.height * 3), 0).save(os.path.join(show, '%s_%s.png' % (u[:-4], h[:6])))
            elif hog.isgz(x) or hog.is_hog(x): walk(x)
    for f in glob.glob(os.path.join(R, 'work', 'iso', 'PSP_GAME', 'USRDIR', 'GAMEDATA', '**', '*.H[OG][GZ]'), recursive=True):
        o = open(f, 'rb').read()
        if hog.isgz(o) or hog.is_hog(o): walk(o)
    print(len(done), sorted(set(done.values())))
if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else None)

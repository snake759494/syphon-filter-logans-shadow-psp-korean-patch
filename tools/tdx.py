"""TDX texture: 0x40 hdr + 0x20 sub-hdr; w@4 h@6 bpp@8 pixsize@0xc; pal rel 0x40+[0x5c], pix rel 0x40+[0x58]"""
import struct
from PIL import Image
def info(d):
    w,h,bpp,ps=struct.unpack_from('<HHII',d,4)
    po,pl=struct.unpack_from('<II',d,0x58)
    return dict(w=w,h=h,bpp=bpp,psize=w*h*bpp//8,pix=0x40+po,pal=0x40+pl,ncol=(po-pl)//4)
def unswizzle(buf,wbytes,h):
    out=bytearray(len(buf)); bw=wbytes//16; i=0
    for by in range(h//8):
        for bx in range(bw):
            for y in range(8):
                o=(by*8+y)*wbytes+bx*16
                out[o:o+16]=buf[i:i+16]; i+=16
    return bytes(out)
def swizzle(buf,wbytes,h):
    out=bytearray(len(buf)); bw=wbytes//16; i=0
    for by in range(h//8):
        for bx in range(bw):
            for y in range(8):
                o=(by*8+y)*wbytes+bx*16
                out[i:i+16]=buf[o:o+16]; i+=16
    return bytes(out)
def decode(d, swz=None):
    I=info(d); w,h,bpp=I['w'],I['h'],I['bpp']
    pal=[tuple(d[I['pal']+4*i:I['pal']+4*i+4]) for i in range(I['ncol'])]
    raw=d[I['pix']:I['pix']+I['psize']]
    if swz is None: swz=bool(struct.unpack_from('<H',d,2)[0]&0) 
    if swz: raw=unswizzle(raw,w*bpp//8,h)
    idx=[]
    if bpp==8: idx=raw
    else:
        for b in raw: idx+= [b&15,b>>4]
    im=Image.new('RGBA',(w,h)); im.putdata([pal[i] for i in idx[:w*h]])
    return im, idx, pal

def encode_like(orig, img, swz=True):
    """orig TDX와 같은 팔레트/크기로 RGBA 이미지를 다시 인코딩"""
    I=info(orig); w,h,bpp=I['w'],I['h'],I['bpp']
    pal=[tuple(orig[I['pal']+4*i:I['pal']+4*i+4]) for i in range(I['ncol'])]
    px=list(img.convert('RGBA').getdata()); cache={}
    def near(c):
        if c in cache: return cache[c]
        if c[3]<8:
            best=min(range(len(pal)),key=lambda i:pal[i][3])
        else:
            best=min(range(len(pal)),key=lambda i:sum((a-b)**2 for a,b in zip(c,pal[i])))
        cache[c]=best; return best
    idx=[near(c) for c in px]
    if bpp==8: raw=bytes(idx)
    else: raw=bytes((idx[i]&15)|((idx[i+1]&15)<<4) for i in range(0,len(idx),2))
    if swz: raw=swizzle(raw,w*bpp//8,h)
    o=bytearray(orig); o[I['pix']:I['pix']+len(raw)]=raw
    return bytes(o)

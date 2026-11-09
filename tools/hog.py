"""HOG: 'iiii', u32 n, u32 off_tbl(0x14), u32 name_tbl, u32 data_base, offsets[n+1] (rel data_base), names\0...
HGZ: 'HGZ\0', u32 total-12, u32 usize, then chunks in 0x8000-byte blocks:
     u32 csize^0xbeef8200, u32 usize^0x3f80feb1, zlib stream; next chunk starts at next 0x8000 boundary"""
import struct, zlib
BLK=0x8000; K1=0xbeef8200; K2=0x3f80feb1
def isgz(d): return d[:4] in (b'HGZ\0',b'HZ2\0')
def unhgz(d):
    assert isgz(d); BLK=0x18000 if d[:3]==b'HZ2' else 0x8000
    tot,us=struct.unpack_from('<II',d,4); o=12; out=bytearray()
    while len(out)<us:
        a,b=struct.unpack_from('<II',d,o); cs=a^K1; ul=b^K2
        u=zlib.decompress(d[o+8:o+8+cs]); assert len(u)==ul
        out+=u; o+=8+cs
        if len(out)<us: o=(o+BLK-1)//BLK*BLK
    return bytes(out)
def hgz(data, level=9, magic=b'HZ2\0'):
    BLK=0x18000 if magic[:3]==b'HZ2' else 0x8000
    out=bytearray(magic+b'\0'*8); pos=0
    while pos<len(data):
        room=BLK-(len(out)%BLK)-8
        # find largest input piece that compresses into room
        rem=len(data)-pos; lo,hi=0,rem; best=None
        g=min(rem, room*3)
        for _ in range(24):
            g=max(1,min(g,hi))
            c=zlib.compress(data[pos:pos+g],level)
            if len(c)<=room:
                best=(g,c); lo=g
                if g==rem or hi-lo<=max(64,lo//64): break
                g=min(hi, max(g+1, int(g*room/max(1,len(c))*0.995)))
                if g<=lo: g=(lo+hi+1)//2
            else:
                hi=g-1
                if hi<=lo: break
                ng=int(g*room/len(c)*0.99)
                g=ng if lo<ng<hi else (lo+hi+1)//2
        if best is None:
            out+=b'\0'*(room+8); continue
        n,c=best
        out+=struct.pack('<II',len(c)^K1,n^K2)+c; pos+=n
        if pos<len(data): out+=b'\0'*((-len(out))%BLK)
    struct.pack_into('<II',out,4,len(out)-12,len(data))
    return bytes(out)
def is_hog(d):
    if len(d)<0x18: return False
    m,n,ot,nt,db=struct.unpack_from('<4sIIII',d,0)
    return ot==0x14 and nt==0x14+4*(n+1) and nt<=db<=len(d) and 0<n<100000
def read(d):
    if isgz(d): d=unhgz(d)
    m,n,ot,nt,db=struct.unpack_from('<4sIIII',d,0); assert is_hog(d)
    offs=struct.unpack_from('<%dI'%(n+1),d,ot)
    names=d[nt:db].split(b'\0')[:n]
    return [(names[i].decode('latin-1'), d[db+offs[i]:db+offs[i+1]]) for i in range(n)], d
def build(items, raw_ref=None):
    """rebuild HOG; layout like original: hdr 0x14, offsets, names, align data_base to 16, members aligned 16"""
    n=len(items); ot=0x14; nt=ot+4*(n+1)
    names=b''.join(nm.encode('latin-1')+b'\0' for nm,_ in items)
    db=(nt+len(names)+15)//16*16
    if raw_ref is not None:
        db=struct.unpack_from('<I',raw_ref,0x10)[0]
        assert db>=nt+len(names)
    offs=[]; body=bytearray()
    for nm,b in items:
        offs.append(len(body)); body+=b; body+=b'\0'*((-len(body))%16)
    offs.append(len(body))
    mg=raw_ref[:4] if raw_ref is not None else b'iiii'
    h=bytearray(struct.pack('<4sIIII',mg,n,ot,nt,db)+struct.pack('<%dI'%(n+1),*offs)+names)
    h+=b'\0'*(db-len(h))
    return bytes(h+body)
if __name__=='__main__':
    import sys
    d=open(sys.argv[1],'rb').read()
    items,raw=read(d)
    for nm,b in items: print('%8d %s'%(len(b),nm))

def repack(data, fn, path=''):
    """컨테이너(HGZ/HOG) 재귀 재구성. fn(memberpath, name, bytes) -> 새 bytes 또는 None(변경없음).
    변경이 없으면 원본 bytes 그대로 반환"""
    gz=data[:4] if isgz(data) else None
    items,raw=read(data)
    changed=False; out=[]
    for n,b in items:
        mp=path+'/'+n
        nb=fn(mp,n,b)
        if nb is None and (is_hog(b) or isgz(b)):
            r=repack(b,fn,mp)
            if r is not b: nb=r
        if nb is not None and nb!=b: changed=True; out.append((n,nb))
        else: out.append((n,b))
    if not changed: return data
    h=build(out,raw)
    return hgz(h,magic=gz) if gz else h

def hgz_names(b):
    try: return b''.join(n.encode() for n, _ in read(b)[0])
    except Exception: return b''

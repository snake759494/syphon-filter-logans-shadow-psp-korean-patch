"""STRINGS.DAT: u32 count, then entries: key\0 (pad4), u32 len(incl \0), text\0 (pad4)"""
import struct
def pad4(n): return (n+3)&~3
def pad8(n): return max(16,(n+3)&~3)
def read(path):
    d=open(path,'rb').read(); n=struct.unpack_from('<I',d,0)[0]; o=4; out=[]
    for i in range(n):
        e=d.index(b'\0',o); k=d[o:e].decode("latin-1"); o=o+pad8(e+1-o)
        ln=struct.unpack_from('<I',d,o)[0]; o+=4
        t=d[o:o+ln]; assert t[-1:]==b'\0',(i,k); o=pad4(o+ln)
        out.append((k,t[:-1]))
    assert o==len(d),(o,len(d))
    return out
def write(path,items):
    b=bytearray(struct.pack('<I',len(items)))
    for k,t in items:
        kb=k.encode('latin-1')+b'\0'; b+=kb+b'\0'*(pad8(len(kb))-len(kb))
        tb=t+b'\0'; b+=struct.pack('<I',len(tb))+tb+b'\0'*(pad4(len(tb))-len(tb))
    open(path,'wb').write(b)
if __name__=='__main__':
    import sys
    for k,t in read(sys.argv[1]): print(k,'=',t.decode('latin-1'))

def parse(d):
    n=struct.unpack_from('<I',d,0)[0]; o=4; out=[]
    for i in range(n):
        e=d.index(bytes(1),o); k=d[o:e].decode('latin-1'); o=o+pad8(e+1-o)
        ln=struct.unpack_from('<I',d,o)[0]; o+=4
        out.append((k,d[o:o+ln-1])); o=pad4(o+ln)
    return out
def dump(items):
    b=bytearray(struct.pack('<I',len(items)))
    for k,t in items:
        kb=k.encode('latin-1')+bytes(1); b+=kb+bytes(pad8(len(kb))-len(kb))
        tb=t+bytes(1); b+=struct.pack('<I',len(tb))+tb+bytes(pad4(len(tb))-len(tb))
    return bytes(b)

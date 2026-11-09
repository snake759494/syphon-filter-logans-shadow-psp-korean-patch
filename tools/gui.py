"""GUI 위젯 텍스트 추출/치환.
위젯: cls\0 'GuiInterfaceDecorator'\0 name\0 pad4, 16B(rect), 4B(flags), text\0 font\0 pad4"""
import re, struct
FONTS={b'Default',b'Callout',b'LargeFnt',b'TinyFnt',b''}
PAT=re.compile(rb'(Gui[A-Za-z]+)\x00GuiInterfaceDecorator\x00')
def p4(n): return (n+3)&~3
def fields(b):
    """yield (text_off, text_end(excl NUL), font, block_end(aligned), cls, name)"""
    for m in PAT.finditer(b):
        cls=m.group(1); o=m.end()
        e=b.index(b'\0',o); name=b[o:e]; o=p4(e+1)
        t0=o+20
        if t0>=len(b): continue
        try:
            te=b.index(b'\0',t0); fe=b.index(b'\0',te+1)
        except ValueError: continue
        font=b[te+1:fe]
        if font not in FONTS: continue
        txt=b[t0:te]
        if any(c<0x20 and c not in (10,) for c in txt): continue
        yield t0,te,font,p4(fe+1),cls.decode(),name.decode('latin-1'),txt
def extract(b):
    return [(t0,txt,font.decode(),cls,name) for t0,te,font,blk,cls,name,txt in fields(b)]
def replace(b, mapping):
    """mapping: t0 offset -> new text bytes. returns new bytes"""
    out=bytearray(); last=0
    for t0,te,font,blk,cls,name,txt in fields(b):
        if t0 not in mapping: continue
        nt=mapping[t0]
        out+=b[last:t0]
        seg=nt+b'\0'+font+b'\0'
        seg+=b'\0'*(p4(t0+len(seg))-(t0+len(seg)))
        # 원래 블록 끝까지의 패딩은 seg에 포함되도록 길이 정렬 (t0는 4정렬)
        assert t0%4==0
        out+=seg; last=blk
    out+=b[last:]
    return bytes(out)

"""SMRK 음성 자막: hdr 12B ('SMRK',u32 0x3000,u32 count|0xcc<<24), rec = 00 00 00 10 '<SCRIPT>' text NUL pad4 + u32 0, 끝 64정렬"""
import re
def parse(b):
    s=[m.start() for m in re.finditer(rb'<SCRIPT>',b)]
    out=[]
    for st in s:
        e=b.index(bytes(1),st); out.append(b[st+8:e])
    return out
def build(orig,texts):
    o=bytearray(orig[:12])
    for t in texts:
        r=bytes([0,0,0,0x10])+b'<SCRIPT>'+t+bytes(1)
        r+=bytes((-len(r))%4)
        o+=r+bytes(4)
    o=o[:-4] if texts else o
    o+=bytes((-len(o))%64)
    if len(o)<len(orig): o+=bytes(len(orig)-len(o))
    return bytes(o)

def build_fixed(orig, texts):
    """각 레코드를 원래 오프셋에 고정. 슬롯을 넘는 텍스트는 None 반환 대신 잘라냄(호출측에서 사전 확인)"""
    s=[m.start() for m in re.finditer(rb'<SCRIPT>',orig)]
    o=bytearray(orig)
    for i,st in enumerate(s):
        end=(s[i+1]-8) if i+1<len(s) else len(orig)
        cap=end-(st+8)-1
        t=texts[i]
        if len(t)>cap:
            t=t[:cap]
            # 2바이트 문자 중간 절단 방지
            j=0
            while j<len(t):
                j+=2 if t[j]>=0xE0 else 1
            if j>len(t): t=t[:-1]
        o[st+8:end]=t+bytes(end-(st+8)-len(t))
    return bytes(o)
def caps(orig):
    s=[m.start() for m in re.finditer(rb'<SCRIPT>',orig)]
    return [((s[i+1]-8) if i+1<len(s) else len(orig))-(st+8)-1 for i,st in enumerate(s)]

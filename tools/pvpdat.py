"""LS_PVP.DAT / COMBAT_OPS_DEMO.DAT 가상 파일시스템 ('HG2\0')
0x20: u32 ?, u32 ?, u32 ent_ptr_tbl_end?, ...  0x30: 엔트리 포인터[n], 0x444: 이름 포인터[n]
엔트리 16B = usize, csize, hash, abs_offset  (현재 모든 파일 usize==csize, 무압축)"""
import struct
def entries(d):
    n = struct.unpack_from('<H', d, 0x20)[0]; et, nt = struct.unpack_from('<2I', d, 0x24)
    ep = struct.unpack_from('<%dI' % n, d, et); npt = struct.unpack_from('<%dI' % (n + 1), d, nt)
    if d[npt[0]] == 0: npt = npt[1:]   # COMBAT_OPS_DEMO.DAT: 이름표 첫 칸이 빈 이름(루트) -> 한 칸 밀림
    else: npt = npt[:n]
    out = []
    for i in range(n):
        a, b, h, o = struct.unpack_from('<IIII', d, ep[i])
        out.append(dict(i=i, name=d[npt[i]:d.index(b'\0', npt[i])].decode(), usize=a, csize=b, hash=h, off=o, ent=ep[i]))
    return out
def get(d, e): return d[e['off']:e['off'] + e['csize']]
def replace(d, repl):
    """repl: {name: bytes} -> 끝에 덧붙이고 엔트리 갱신"""
    d = bytearray(d); E = {e['name']: e for e in entries(d)}
    for nm, b in repl.items():
        e = E[nm]
        while len(d) % 16: d.append(0)
        off = len(d); d += b
        struct.pack_into('<III', d, e['ent'], len(b), len(b), e['hash']); struct.pack_into('<I', d, e['ent'] + 12, off)
    while len(d) % 2048: d.append(0)
    return bytes(d)
if __name__ == '__main__':
    import sys
    d = open(sys.argv[1], 'rb').read()
    for e in entries(d): print(e['i'], e['name'], e['csize'], hex(e['off']), get(d, e)[:4])

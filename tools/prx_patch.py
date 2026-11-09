"""LS.PRX 패치: 한글 글리프 공유
- 한글 글리프(코드포인트 >= 0x180)는 DEFAULT 글꼴에만 존재.
- 글리프 조회(0x2cfa4c)에서 못 찾은 0x180 이상 코드는 '한글 글꼴'(G)에서 다시 조회.
- G 는 글꼴 테이블 빌더 끝에서 font+0xc8(상위바이트 3 표)이 있으면 기록.
- 다른 글꼴 FNT의 페이지 목록에 같은 순서로 한글 페이지 이름을 붙여 두므로 페이지 인덱스가 일치.
- 공간: 생성자(0x2cfab0)를 압축해 확보한 뒷부분 + 조회 함수 자리. 0x58a05c 이후 .text 는 실행 중 지워져 사용 불가."""
import struct, sys, os
from keystone import Ks, KS_ARCH_MIPS, KS_MODE_MIPS32, KS_MODE_LITTLE_ENDIAN
ks = Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + KS_MODE_LITTLE_ENDIAN)
REG = {n: i for i, n in enumerate('zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split())}
TOFF = 0x74
def _r(x): return REG[x.strip().lstrip('$')]
BR = {'b': (4, 0, 0), 'beq': (4, 2, 0), 'bne': (5, 2, 0), 'beqz': (4, 1, 0), 'bnez': (5, 1, 0), 'blez': (6, 1, 0), 'bgtz': (7, 1, 0),
      'bltz': (1, 1, 0), 'bgez': (1, 1, 1), 'bal': (1, 0, 0x11)}
def asm(src, addr, ext=None):
    lines = [l.split('#')[0].strip() for l in src.strip().splitlines()]
    lab = dict(ext or {}); pc = addr; body = []
    for l in lines:
        if not l: continue
        if l.endswith(':'): lab[l[:-1]] = pc; continue
        body.append((pc, l)); pc += 4
    out = b''
    for pc, l in body:
        op, _, args = l.partition(' '); a = [x.strip() for x in args.split(',')] if args.strip() else []
        def tgt(t):
            v = lab[t] if t in lab else int(t, 0)
            off = (v - (pc + 4)) >> 2; assert -0x8000 <= off < 0x8000, l; return off & 0xffff
        if op in BR:
            opc, nr, rt = BR[op]
            if op == 'b': w = (4 << 26) | tgt(a[0])
            elif op == 'bal': w = (1 << 26) | (0x11 << 16) | tgt(a[0])
            elif op in ('bltz', 'bgez'): w = (1 << 26) | (_r(a[0]) << 21) | (rt << 16) | tgt(a[1])
            elif nr == 2: w = (opc << 26) | (_r(a[0]) << 21) | (_r(a[1]) << 16) | tgt(a[2])
            else: w = (opc << 26) | (_r(a[0]) << 21) | tgt(a[1])
            out += struct.pack('<I', w)
        elif op == 'li32':   # li32 reg, value (lui+ori, 2 words)
            v = int(a[1], 0) & 0xffffffff
            out += bytes(ks.asm('.set noreorder; lui %s, 0x%x; ori %s, %s, 0x%x' % (a[0], v >> 16, a[0], a[0], v & 0xffff), pc)[0])
        else:
            enc, _ = ks.asm('.set noreorder; ' + l, pc); assert len(enc) == 4, (l, len(enc)); out += bytes(enc)
    return out, lab

LOOKUP = 0x2cfa4c; LOOKUP_END = 0x2cfab0
CTOR = 0x2cfab0; CTOR_END = 0x2cfb94      # 글꼴 생성자: 같은 동작으로 압축해 뒷부분을 빈 공간으로 확보
BUILD_EPI = 0x2cf40c
# 주의: 0x58a05c 이후 .text 는 실행 중 지워짐(재사용) -> 코드 동굴로 못 씀
CTOR_SRC = r"""
    lui   $a1, 0x65
    addiu $a1, $a1, -0x1884
    sw    $a1, 0x4cc($a0)
    sw    $zero, 0x80($a0)
    sw    $zero, 0x84($a0)
    sw    $zero, 0x88($a0)
    sw    $zero, 0x8c($a0)
    ori   $a1, $zero, 0xfffd
    sw    $a1, 0xa4($a0)
    addiu $a1, $zero, -1
    sw    $a1, 0xa8($a0)
    sw    $zero, 0x4bc($a0)
    lui   $a1, 0x4000
    sw    $a1, 0x4c0($a0)
    lui   $a1, 0xc000
    sw    $a1, 0x4c4($a0)
    sb    $zero, 0x4c8($a0)
    lui   $a2, 0x3f00
    lui   $a3, 0x3f80
    move  $a1, $a0
    addiu $t0, $a0, 0x80
c1:
    sw    $a2, 0($a1)
    sw    $a2, 4($a1)
    sw    $a2, 8($a1)
    sw    $a3, 0xc($a1)
    addiu $a1, $a1, 0x10
    bne   $a1, $t0, c1
    nop
    addiu $a1, $a0, 0xac          # 0xac..0x4b8 0 으로(원래 0xac~0xb8 개별 저장 + 0xbc~ 루프)
    addiu $t0, $a0, 0x4bc
c2:
    sw    $zero, 0($a1)
    addiu $a1, $a1, 4
    bne   $a1, $t0, c2
    nop
    jr    $ra
    move  $v0, $a0
free:
"""
# 빈 공간: G(한글 글꼴 포인터) + 빌더 훅 + 조회 D 경로
FREE_SRC = r"""
gvar:
    nop
bhook:                           # 한글 표(+0xc8)가 있는 글꼴: G 가 비었거나 해제된 객체(+0x4cc vtable==0)일 때만 G 로 기록
    bal   bh1
    lw    $a0, 0xc8($s0)
bh1:
    beqz  $a0, bhd
    lw    $a1, %(g1)d($ra)
    beqz  $a1, bhs
    nop
    lw    $a2, 0x4cc($a1)
    bnez  $a2, bhd
    nop
bhs:
    sw    $s0, %(g1)d($ra)
bhd:
    lw    $s0, 0x100($sp)
    b     epi2
    lw    $s1, 0x104($sp)
dpath:
    lw    $a1, 0xa8($a0)
    lw    $a2, 0xac($a0)
    slti  $a0, $a1, 0
    movn  $a2, $zero, $a0
    b     fpath
    movn  $a1, $zero, $a0
"""
# 새 조회 함수: 현재 글꼴에서 먼저 찾고(표 없음/글자 없음이면) G 에서 다시 찾음. 둘 다 실패하면 기본 글리프.
# 레지스터는 a0-a3, v0 만 사용(호출측이 t0/v1 등을 살려 둔다고 가정). 반환은 jr v0. 반환은 jr v0 (ra 는 호출측이 어차피 파괴된다고 봄)
LOOK_SRC = r"""
    move  $v0, $ra
    bal   lk1
    andi  $a3, $a1, 0xffff
lk1:
    sra   $a1, $a3, 8
    sll   $a1, $a1, 2
    addu  $a1, $a0, $a1
    lw    $a2, 0xbc($a1)
    beqz  $a2, useg
    andi  $a1, $a3, 0xff
    addu  $a1, $a1, $a1
    addu  $a2, $a2, $a1
    lh    $a1, 0($a2)
    bgez  $a1, fpath
    lw    $a2, 0xac($a0)
useg:
    lw    $a2, %(g2)d($ra)
    beq   $a2, $a0, dpath
    nop
    beqz  $a2, dpath
    nop
    b     lk1
    move  $a0, $a2
fpath:
    sll   $a1, $a1, 3
    jr    $v0
    addu  $v0, $a2, $a1
"""
EPI_SRC = r"""
    b     bhook
    nop
"""
def patch(prx):
    """LS.PRX / LS_PVP.PRX 공용: 원본 조회 함수 바이트로 위치를 찾아 같은 상대 배치로 적용"""
    d = bytearray(prx)
    ph = struct.unpack_from('<I', d, 0x1c)[0]; TOFF = struct.unpack_from('<I', d, ph + 4)[0]
    ref = bytes.fromhex('ffffa730ffffe730')   # andi a3,a1,0xffff ; andi a3,a3,0xffff
    i = d.find(ref); assert i > 0 and d.find(ref, i + 1) < 0
    D = (i - TOFF) - LOOKUP
    LK, LKE, CT, CTE, EP = LOOKUP + D, LOOKUP_END + D, CTOR + D, CTOR_END + D, BUILD_EPI + D
    assert d[TOFF+EP:TOFF+EP+4] == asm('lw $s0, 0x100($sp)', 0)[0]
    orig2 = bytes(d[TOFF+CT:TOFF+CT+8])          # 생성자 첫 2워드(vtable 주소, 재배치 대상) 보존
    assert orig2[2:4] == bytes.fromhex('053c') and orig2[6:8] == bytes.fromhex('a524'), orig2.hex()
    ctor, cl = asm(CTOR_SRC, CT); ctor = orig2 + ctor[8:]; FREE = cl['free']
    ext = {"epi2": EP + 8}
    _, fl = asm(FREE_SRC % dict(g1=0), FREE, dict(ext, fpath=FREE))
    _, ll = asm(LOOK_SRC % dict(g2=0), LK, dict(dpath=fl['dpath']))
    g = fl['gvar']
    free = asm(FREE_SRC % dict(g1=g - fl['bh1']), FREE, dict(ext, fpath=ll['fpath']))[0]
    look = asm(LOOK_SRC % dict(g2=g - ll['lk1']), LK, dict(dpath=fl['dpath']))[0]
    free = bytes(4) + free[4:]
    assert len(look) <= LKE - LK and FREE + len(free) <= CTE, (len(look), hex(FREE + len(free)))
    epi = asm(EPI_SRC, EP, dict(bhook=fl['bhook']))[0]
    parts = os.environ.get('KPARTS', 'LB')
    d[TOFF+CT:TOFF+CTE] = ctor + bytes(CTE - CT - len(ctor))
    d[TOFF+FREE:TOFF+FREE+len(free)] = free
    if 'L' in parts:
        d[TOFF+LK:TOFF+LKE] = look + bytes(LKE - LK - len(look))
    if 'B' in parts:
        d[TOFF+EP:TOFF+EP+len(epi)] = epi
    # 재배치가 패치 영역 안에 없는지 (생성자 첫 2워드 제외)
    sh = struct.unpack_from('<I', d, 0x20)[0]
    s = struct.unpack_from('<10I', d, sh+2*40)
    assert s[1] == 0x700000a0
    for j in range(s[5]//8):
        off, info = struct.unpack_from('<II', d, s[4]+j*8)
        for a, b in ((LK, LKE), (EP, EP+8), (CT+8, CTE)):
            assert not (a <= off < b), hex(off)
    return bytes(d)
if __name__ == '__main__':
    p = patch(open(sys.argv[1], 'rb').read()); open(sys.argv[2], 'wb').write(p); print('ok')

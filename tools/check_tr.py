"""번역 결과 검사: python tools/check_tr.py work/tr/in_XX.json work/tr/out_XX.json
- 모든 원문 키 존재, 서식 코드 보존, 허용 문자(한글 음절, ASCII), MRK 바이트 길이(한글 2바이트) <= 원문"""
import sys, json, re
CODE = re.compile(r'<[pcn](?::[^>]*)?>|%[-0-9.]*[a-zA-Z]|\n|^@')
def blen(s): return sum(2 if 0xAC00 <= ord(c) <= 0xD7A3 else len(c.encode('utf-8')) for c in s)
def main(fi, fo):
    I = json.load(open(fi, encoding='utf-8')); O = json.load(open(fo, encoding='utf-8'))
    bad = 0
    for e in I:
        en = e['en']
        if en not in O: print('MISSING', repr(en[:70])); bad += 1; continue
        ko = O[en]
        if not isinstance(ko, str) or not ko.strip(): print('EMPTY', repr(en[:70])); bad += 1; continue
        if sorted(CODE.findall(en)) != sorted(CODE.findall(ko)):
            print('CODE', repr(en[:70]), sorted(CODE.findall(en)), sorted(CODE.findall(ko))); bad += 1
        odd = [c for c in ko if not (c == '\n' or 0x20 <= ord(c) < 0x7f or 0xAC00 <= ord(c) <= 0xD7A3)]
        if odd: print('CHAR', repr(en[:50]), ''.join(sorted(set(odd)))); bad += 1
        if e['src'].startswith('mrk') and blen(ko) > len(en.encode('utf-8')):
            print('LONG(%d>%d)' % (blen(ko), len(en.encode('utf-8'))), repr(en[:70]), '=>', ko); bad += 1
    extra = set(O) - {e['en'] for e in I}
    if extra: print('EXTRA keys', len(extra))
    print('total', len(I), 'problems', bad)
if __name__ == '__main__': main(sys.argv[1], sys.argv[2])

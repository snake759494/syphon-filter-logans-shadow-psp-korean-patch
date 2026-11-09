"""번역문 인코딩: 한글 음절 -> 코드포인트(0x180+k) UTF-8 2바이트, 나머지 UTF-8 그대로"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import kfont
def is_hangul(ch): return 0xAC00 <= ord(ch) <= 0xD7A3
def needed_chars(texts):
    s = set()
    for t in texts:
        for ch in t:
            if is_hangul(ch): s.add(ch)
    return sorted(s)
class Enc:
    def __init__(self, chars):
        self.chars = chars; self.m = {ch: kfont.BASE_CP+i for i, ch in enumerate(chars)}
    def enc(self, t):
        out = []
        for ch in t:
            if ch in self.m: out.append(chr(self.m[ch]))
            else:
                assert not is_hangul(ch), ch
                out.append(ch)
        return ''.join(out).encode('utf-8')

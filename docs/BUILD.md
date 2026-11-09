# 빌드 방법

번역 대본·원문은 저장소에 없으므로, 아래는 자신이 가진 원본과 번역 파일로 다시 빌드하는 절차입니다.

## 준비물
- 원본 ISO `Syphon Filter - Logan's Shadow (USA).iso` (MD5 `ac7f63f53c43d6cfd330f0bf7ee30f8f`)
- Python 3.12+ : `pip install pillow numpy pycdlib keystone-engine capstone websocket-client`
- 글꼴: `NanumSquareNeo-bRg.ttf` (작업 폴더), `Galmuri11.ttf`·`Galmuri11-Bold.ttf` (`work/fonts/ttf/`)

## 폴더 구성
```
<작업 폴더>/
  Syphon Filter - Logan's Shadow (USA).iso
  NanumSquareNeo-bRg.ttf
  tools/        (이 저장소의 tools)
  trans/        ko.json, mrk_short.json, prx_str.json, meta.json, tex/  (번역 — 저장소 미포함)
  work/         iso/, fonts/ttf/, src/
```

## 순서
1. ISO 풀기: `python tools/extract_iso.py "Syphon Filter - Logan's Shadow (USA).iso" work/iso`
2. 원문 추출: `python tools/extract_text.py` → `work/src/all.json`, 멀티플레이·체험판은 `python tools/pvp_extract.py [DAT 경로] [출력 이름]`
3. 번역 파일 작성 (`docs/TRANSLATION_GUIDE.md`)
   - `ko.json`: `{영어 원문: 번역}` — STRINGS·MRK·GUI·SUB 공통
   - `mrk_short.json`: 원래 길이를 넘는 MRK 대사의 줄인 번역
   - `prx_str.json`: 실행 파일 내장 문자열 `{영어: 번역}` (원래 길이 이하)
   - `meta.json`: `{"title": "..."}`
   - 검사: `python tools/check_tr.py 입력.json 번역.json`
4. 그림 글자: `python tools/texko.py` → `trans/tex/`
5. 빌드: `python tools/build.py` → `Syphon Filter - Logan's Shadow (Korean).iso`
6. 검사: `python tools/audit.py`
7. 차분: `xdelta3 -0 -f -e -s 원본.iso 한글.iso 패치.xdelta`

PPSSPP 원격 디버거로 자동 확인할 때는 `python tools/emu.py` 를 씁니다.

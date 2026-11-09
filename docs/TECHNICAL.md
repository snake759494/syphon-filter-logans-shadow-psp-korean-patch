# 기술 문서

## 파일 구성
- `PSP_GAME/USRDIR/LS.PRX` — 본편 실행 파일. 멀티플레이 `LS_PVP/LS_PVP.PRX`, 체험판 `COMBAT_OPS/COMBAT_OPS_DEMO.PRX` 도 같은 엔진.
- `GAMEDATA/**/*.HOG` / `*.HGZ` — 묶음 파일(HGZ = 압축 HOG, 매직 `HZ2\0`). 안에 STRINGS.DAT·MRK·GUI·FNT·TDX 가 들어 있음 (`tools/hog.py`).
- `LS_PVP.DAT`, `COMBAT_OPS_DEMO.DAT` — HG2 가상 파일시스템. 항목 수 u16 @0x20, 표 오프셋 @0x24/0x28. 체험판은 이름 표가 한 칸 밀려 있음(첫 이름이 빈 문자열) (`tools/pvpdat.py`).
- `*.SUB` — 컷신 동영상 자막. `%FEED ENGLISH` 구간의 따옴표 줄을 교체. 줄 끝이 CRLF 이므로 정규식에서 `\r` 을 허용해야 함.

## 문자 인코딩
한글 음절은 필요한 것만 모아 코드포인트 0x180 이상에 2바이트로 배정합니다 (`tools/kenc.py`). MRK 음성 자막과 실행 파일 문자열은 원래 바이트 길이 안에 들어가야 합니다.

## 글꼴
- `FONTS_PSP.HOG`(메뉴·공통), `FONTS.HGZ`/`FONTS2.HGZ`, `FONTS_RP.HGZ`(스토리 레벨에서 남는 글꼴 묶음)를 모두 교체. `FONTS_PS2.HOG` 는 PS2용(FNT v4.0)이라 PSP에서 쓰지 않음.
- 글꼴 묶음이 약 **240KB** 를 넘으면 실행 중 힙이 깨져 부팅 단계에서 멈춤. 그래서 한글 글리프 레코드는 DEFAULT(FONTS_RP 는 DEFAULT·CALLOUT·TINYFNT)에만 넣고, 나머지 글꼴은 같은 순서로 한글 텍스처 페이지(KDEF_*) 이름만 붙임 (`tools/build.py` `kfont_hog`).

## 실행 파일 패치 (`tools/prx_patch.py`)
- 글리프 조회 함수(0x2cfa4c)를 새로 작성: 현재 글꼴의 상위바이트 표에서 먼저 찾고, 표가 없거나 항목이 음수면 '한글 글꼴' G 에서 다시 찾음. 둘 다 실패하면 기본 글리프. a0–a3·v0 만 쓰고 `jr v0` 로 복귀.
- G 는 글꼴 표 빌더 끝(0x2cf40c)에 건 훅에서 기록. 한글 표(+0xc8)가 있는 글꼴이면서, G 가 비었거나 이미 해제된 객체(+0x4cc vtable == 0)일 때만 갱신 — 레벨 전환으로 해제된 글꼴을 가리켜 브리핑 한글이 사라지던 문제 대응.
- 공간은 글꼴 생성자(0x2cfab0)를 같은 동작으로 압축해(0 채우기 루프를 0xac 부터) 확보. 0x58a05c 이후 .text 는 실행 중 재사용되므로 코드 동굴로 못 씀.
- 원본 조회 함수 바이트로 위치를 찾아 상대 배치로 적용하므로 세 PRX 에 같은 패치가 들어감. 재배치 항목이 패치 영역에 없는지 검사.

## 텍스트
- STRINGS.DAT (`tools/strdat.py`), MRK 음성 자막 (`tools/mrk.py`, 슬롯 고정 길이), GUI 레이아웃 (`tools/gui.py`).
- 실행 파일 내장 문자열은 제자리 교체(원래 길이 이하).
- PARAM.SFO 의 TITLE 교체.

## 그림 글자
TDX 텍스처(`tools/tdx.py`)를 풀어 영어 글자를 지우고 한글을 그린 뒤 같은 크기로 다시 인코딩 (`tools/texko.py`). 빌드 시 원본 MD5 로 찾아 교체.

## ISO
`tools/isobuild.py` 가 원본 ISO에서 바뀐 파일만 교체해 새 ISO를 만듭니다(크기가 커진 파일은 뒤쪽에 재배치).

# 사이폰 필터: 로건스 섀도우 (PSP) 비공식 한글패치

PSP 북미판 **Syphon Filter: Logan's Shadow (사이폰 필터: 로건스 섀도우, UCUS-98606)** 비공식 한국어 패치입니다. 이 저장소에는 제작 도구와 기술 문서만 있고, 패치 파일(xdelta)은 [Releases](../../releases)에서 받을 수 있습니다. 게임 원본·영어 원문·번역 대본은 포함하지 않습니다.

## 적용 방법
1. 아래 해시와 일치하는 **원본 `.iso`** 를 준비합니다. (CSO·CHD 등으로 변환한 이미지에는 적용할 수 없습니다.)
   - PowerShell: `Get-FileHash -Algorithm MD5 -LiteralPath ".\Syphon Filter - Logan's Shadow (USA).iso"`
2. xdeltaUI 같은 도구로 원본 `.iso` 에 `SyphonFilter_LogansShadow_KO_v1.0.xdelta` 를 적용합니다. (Patch = xdelta, Source File = 원본 ISO, Output File = 새 파일명)
   - 명령줄: `xdelta3 -d -s "Syphon Filter - Logan's Shadow (USA).iso" SyphonFilter_LogansShadow_KO_v1.0.xdelta "Syphon Filter - Logan's Shadow (Korean).iso"`
3. 만들어진 ISO를 PPSSPP 또는 커스텀 펌웨어(PSP·PS Vita Adrenaline 등)에서 실행합니다.

| 항목 | 값 |
| --- | --- |
| 원본 ISO 크기 | 1,293,877,248 바이트 |
| 원본 ISO MD5 | `ac7f63f53c43d6cfd330f0bf7ee30f8f` |
| 원본 ISO SHA-256 | `e5eead538ea0bacd19052dbfd413b2bbd0d56cfe09614cd9329c6df634a5fabe` |
| xdelta SHA-256 | `0dcfde348d2c57df2025a687910354892e465ca61793f15f182357b077f62e8b` |
| 결과 ISO 크기 | 1,465,327,616 바이트 |
| 결과 ISO SHA-256 | `e54c36427cc0835a05c87bc90d0955baf204aa4929c4da2ff75c8dcd2cb7fae7` |

## 주의
- PPSSPP에서만 확인했습니다. 실기(커스텀 펌웨어 포함)에서는 확인하지 못했습니다.
- 원본에서 만든 **상태저장(세이브 스테이트)** 은 불러오지 마세요. 일반 세이브는 그대로 쓸 수 있습니다.
- 음성 자막은 기본값이 꺼져 있습니다. **옵션 → 오디오 → 자막** 을 켜면 무전·컷신 대사가 한국어 자막으로 나옵니다.
- xdelta는 압축하지 않은 형식(`-0`)입니다(약 158MB).

## 한글화 내용
- 메뉴·옵션·무기·장비·도움말·레벨 브리핑·목표·정보 문서 등 STRINGS 문자열 3,879종 직접 번역
- 음성 대사 자막(MRK) 2,417종 전수 번역 — 원래 자리 길이를 넘는 대사 21개는 뜻을 살려 줄여 씀
- 컷신 동영상 자막(SUB) 7개 파일 517줄
- 화면 레이아웃(GUI) 문자열, 실행 파일 내장 문자열(UMD 안내·프로필 저장 안내 등)
- 멀티플레이 모드(LS_PVP) 메뉴·안내 문자열 약 900종
- 메인 메뉴 「미리 보기」의 **Combat Ops 체험판** 메뉴·안내 문자열
- 그림 글자 — 상호작용 아이콘(암호·스캔·카드), 준비 중 임무 썸네일 9장, SCE 「제공」 화면
- 홈 메뉴 게임 이름 「사이폰 필터: 로건스 섀도우」
- 한글 글리프는 본문 글꼴(DEFAULT)에 넣고, 실행 파일(LS.PRX·LS_PVP.PRX·COMBAT_OPS_DEMO.PRX)의 글리프 조회 함수를 고쳐 다른 글꼴도 같은 한글 글리프를 쓰도록 함
- 글꼴: 한글 본문 갈무리11, 아이콘 그림 글자 갈무리11 Bold, 「제공」 화면 나눔스퀘어네오

## 그대로 둔 것
- 음성, 실제 총기 모델명·코드명 같은 고유 표기, 개발용 자리표시 문자열, 영문 로고 이미지, 레벨 배경 안의 표지판 글자(FIRST AID 등)

## 검증 범위
PPSSPP에서 타이틀, 메뉴, 옵션, 훈련 1(브리핑·음성 자막), 스토리 에피소드 1(브리핑·엔진 컷신 자막·인게임 자막·HUD), 멀티플레이 메뉴, Combat Ops 체험판 메뉴를 확인했습니다. MRK·STRINGS·GUI·SUB 파일을 전수 검사해 번역 대상 영어가 남지 않고 잘린 대사가 없는 것을 확인했습니다. 컷신 동영상 자막은 파일 단위로만 확인했고 재생 화면은 보지 못했습니다. 전체 플레이 검증은 하지 않았습니다. 문제를 발견하면 Issues에 알려 주세요.

## 문서
- [CHANGELOG.md](CHANGELOG.md) — 변경 기록
- [docs/TECHNICAL.md](docs/TECHNICAL.md) — 파일 형식과 한글화 방법
- [docs/BUILD.md](docs/BUILD.md) — 직접 빌드하는 방법
- [docs/TRANSLATION_GUIDE.md](docs/TRANSLATION_GUIDE.md) — 번역 지침
- [docs/FONT_CREDITS.md](docs/FONT_CREDITS.md) — 글꼴
- [RIGHTS.md](RIGHTS.md) — 권리 및 외부 자료

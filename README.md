# StockBizView - AI 자동 주식 리포트 발행 시스템

> 한국/미국 시장 데이터를 수집하고, AI(Claude)가 세계적 투자 애널리스트 수준의 분석 리포트를 생성하여 WordPress에 자동 발행하는 시스템

## 시스템 구조

```
[Yahoo Finance API] → collect_data.py → latest_market_data.json
                                              ↓
                                        ai_analyst.py (Claude API, 3회 재시도)
                                              ↓
                                        generate_report.py (HTML 생성)
                                              ↓
                                        publish_wp.py (WordPress 발행 + 캐시 퍼지)
                                              ↓
                                        update_homepage.py (홈페이지 실시간 업데이트)

[Finnhub API + 정적 데이터] → market_calendar.py → WordPress 마켓 캘린더 페이지

auto_publish.py ← 위 전체를 통합 실행하는 메인 파이프라인
```

## 파일 구조

```
Stock_auto/
├── auto_publish.py           # 통합 파이프라인 (수집→분석→생성→발행)
├── collect_data.py           # 시장 데이터 수집 (Yahoo Finance v8 API)
├── ai_analyst.py             # AI 분석 생성 (Anthropic Claude API)
├── generate_report.py        # HTML 리포트 생성 (인라인 CSS, 다크 테마)
├── publish_wp.py             # WordPress REST API 발행 + Breeze 캐시 퍼지
├── update_homepage.py        # 홈페이지 티커바/Market Pulse 실시간 업데이트
├── market_calendar.py        # 마켓 캘린더 (경제지표, 어닝, 옵션만기)
├── latest_market_data.json   # 최근 수집 데이터 (자동 생성, .gitignore)
├── publish_log.jsonl         # (레거시, 미사용 — 중복 체크는 WordPress API로 수행)
├── .github/
│   └── workflows/
│       ├── daily_reports.yml     # 매일 장전/장후 리포트
│       └── weekly_reports.yml    # 주간 리포트 4종
└── README.md
```

## 리포트 종류 (6종)

| 타입 | AI 페르소나 | 발행 스케줄 (KST) | WP 카테고리 ID |
|------|------------|-------------------|---------------|
| `pre_market` | 골드만삭스/모건스탠리 수석 애널리스트 | 매일 06:50 (7시 발행 목표) | 2 |
| `post_market` | 삼성증권/미래에셋 리서치센터 수석 | 매일 19:03 | 3 |
| `us_market` | 월가 최고 투자 전략가 | 화/금 09:13 | 7 |
| `korea_market` | 한국 증권사 리서치센터장 | 월/목 19:33 | 6 |
| `stock_analysis` | 증권사 기업분석 수석 | 화/금 19:47 | 4 |
| `investment_strategy` | 글로벌 자산운용사 CIO | 수 09:07 | 5 |

**주간 총 발행량**: 일 2건 × 5일 + 주간 4종 = **약 14건/주**

## 수집 데이터

### 지수
- KOSPI (`^KS11`), KOSDAQ (`^KQ11`)
- S&P 500 (`^GSPC`), NASDAQ (`^IXIC`), 다우존스 (`^DJI`)

### 원자재/환율
- USD/KRW, WTI 원유, 금, 비트코인, VIX 공포지수, 미국 10년물 금리, 달러인덱스

### 주요 종목
- **한국**: 삼성전자, SK하이닉스, NAVER, 카카오, 현대차, 셀트리온, 삼성SDI, 포스코퓨처엠, 신한지주, KB금융
- **미국 Mag7**: Apple, Microsoft, Alphabet, Amazon, NVIDIA, Meta, Tesla

## 실행 방법

### 로컬 실행

```bash
# 전체 파이프라인 (수집 → AI 분석 → HTML 생성 → WordPress 발행)
python auto_publish.py post_market publish

# 리포트 타입: pre_market, post_market, us_market, korea_market, stock_analysis, investment_strategy
# 상태: publish (즉시 발행) 또는 draft (초안)

# 개별 모듈 실행
python collect_data.py                    # 데이터 수집만
python ai_analyst.py post_market          # AI 분석만
python update_homepage.py                 # 홈페이지 업데이트만
python market_calendar.py                 # 마켓 캘린더 업데이트
python market_calendar.py --test          # 캘린더 데이터 확인 (발행 X)
```

### GitHub Actions 자동화

GitHub 리포지토리에 push하면 cron 스케줄에 따라 자동 실행됩니다.
수동 실행: Actions 탭 → 워크플로우 선택 → Run workflow

## 환경 변수 (Secrets)

### 필수

| 변수 | 설명 |
|------|------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API 키 |
| `WP_URL` | WordPress URL (`https://stockbizview.com`) |
| `WP_USER` | WordPress 사용자 이메일 |
| `WP_APP_PASSWORD` | WordPress Application Password |
| `FINNHUB_API_KEY` | Finnhub API 키 (마켓 캘린더 어닝 데이터) |

### 선택 (Cloudways 캐시 자동 퍼지)

| 변수 | 설명 |
|------|------|
| `CLOUDWAYS_EMAIL` | Cloudways 계정 이메일 |
| `CLOUDWAYS_API_KEY` | Cloudways API 키 |
| `CLOUDWAYS_SERVER_ID` | Cloudways 서버 ID |
| `CLOUDWAYS_APP_ID` | Cloudways 앱 ID |

## 인프라

- **호스팅**: Cloudways (DigitalOcean)
- **CMS**: WordPress 6.x + twentytwentyfive 테마 (FSE)
- **캐시**: Breeze 플러그인 (TTL: 60분) + Object Cache Pro (Redis)
- **AI**: Anthropic Claude (`claude-sonnet-4-6`)
- **CI/CD**: GitHub Actions (cron 스케줄)
- **도메인**: stockbizview.com
- **서버 IP**: 158.247.221.235

## 기술 구현 상세

### 파이프라인 (`auto_publish.py`)

```
Step 1/5: 시장 데이터 수집 (Yahoo Finance)
Step 2/5: 홈페이지 실시간 업데이트 (티커바 + Market Pulse)
  └── 2.5: 마켓 캘린더 주간 업데이트 (월요일 장전에만 실행)
Step 0/5: WordPress API 중복 발행 체크
Step 3/5: AI 애널리스트 분석 생성 (Claude API)
  └── 실패/품질 미달 시 발행 차단 (빈 리포트 발행 방지)
Step 4/5: HTML 리포트 생성
Step 5/5: WordPress 발행 + 캐시 퍼지
```

### 데이터 수집 (`collect_data.py`)
- Yahoo Finance v8 Chart API (`query1.finance.yahoo.com/v8/finance/chart/`)
- 1일 변동률: `closes[-2]` 기준 (chartPreviousClose는 range 기준이라 부정확)
- User-Agent 헤더 필수, 10초 타임아웃
- 종목별 독립 try/except — 개별 실패가 전체 수집을 중단하지 않음

### AI 분석 (`ai_analyst.py`)
- 리포트 타입별 전용 프롬프트 (골드만삭스/모건스탠리/삼성증권 등 페르소나)
- JSON 형식 응답 → 파싱 (코드블록 제거, `{`~`}` 추출, fallback)
- max_tokens: 8,000 / timeout: 300초 (5분)
- **안정성**: 3회 재시도 + 5초 딜레이, 전체 실패 시 발행 차단 (빈 리포트 방지)

### HTML 리포트 (`generate_report.py`)
- 완전 인라인 CSS (twentytwentyfive 테마 override 위해 `!important` 사용)
- 다크 테마 (#0d1117 배경, #f0f6fc 전경)
- 반응형: metric cards, bar charts, 테이블
- AI 내러티브 섹션: 시황분석, 섹터분석, 리스크, 전략, 전망
- 제목: AI 생성 제목 + 날짜 (카테고리 태그 없음)

### WordPress 발행 (`publish_wp.py`)
- REST API v2 (`/wp-json/wp/v2/posts`)
- Basic Auth (Application Password)
- 카테고리 자동 배정, 태그 생성/검색
- 리포트 타입별 SEO excerpt 자동 생성
- **중복 방지**: WordPress API로 오늘 같은 카테고리 발행 여부 확인
- 발행 후 Breeze 캐시 퍼지

### 홈페이지 업데이트 (`update_homepage.py`)
- WordPress FSE 템플릿 API로 home 템플릿 직접 수정
- 티커바: KOSPI, KOSDAQ, S&P 500, NASDAQ, USD/KRW, BTC
- Market Pulse: VIX, WTI, 금, US 10Y, 달러인덱스, 비트코인
- 리포트 발행 시마다 자동 갱신

### 마켓 캘린더 (`market_calendar.py`)
- **경제지표**: FOMC, CPI, NFP, PPI, GDP, ISM 등 (연간 확정 일정, 정적 JSON)
- **어닝 시즌**: Finnhub API 실시간 수집
- **한국 이벤트**: BOK 금통위, 옵션만기일 (매월 둘째 목요일)
- **휴장일**: 한국/미국 공휴일
- 주간 그룹 HTML 생성 — THIS WEEK 배지, HIGH/MED/INFO 임팩트 표시
- WordPress 페이지 ID 10에 자동 업데이트
- **실행 주기**: 매주 월요일 장전 리포트 발행 시 자동 갱신

## WordPress 구조

### 카테고리 계층
```
홈
├── 데일리 리포트
│   ├── 장전 리포트 (ID: 2)
│   └── 장후 리포트 (ID: 3)
├── 한국 시장 (ID: 6)
│   ├── KOSPI 시황 (ID: 9)
│   ├── KOSDAQ 시황 (ID: 10)
│   ├── 업종별 분석 (ID: 11)
│   └── 수급 동향 (ID: 12)
├── 미국 시장 (ID: 7)
│   ├── S&P 500 시황 (ID: 13)
│   ├── NASDAQ 시황 (ID: 14)
│   ├── 섹터별 분석 (ID: 15)
│   ├── 매크로 지표 (ID: 16)
│   └── 어닝 시즌 (ID: 17)
├── 투자 전략 (ID: 5)
├── 종목 분석 (ID: 4)
└── 마켓 캘린더 (페이지 ID: 10)
```

### UX 디자인 (Jakob Nielsen 원칙 적용)
- **홈**: Masthead + 데스크 내비게이션 (6개 카테고리) + 방법론 푸터
- **아카이브**: 브레드크럼 + 카테고리 설명 + 12건 3열 그리드 + 페이지네이션
- **싱글 포스트**: 브레드크럼 + 타이틀 퍼스트 + 900px 본문폭 + 이전/다음 네비게이션
- **읽기 경험**: 리딩 프로그레스 바 + 스크롤-투-탑 버튼

## 에러 처리 및 안정성

| 실패 지점 | 처리 방식 |
|-----------|----------|
| 개별 종목 데이터 수집 실패 | 해당 종목만 스킵, 나머지 정상 수집 |
| Claude API 타임아웃/오류 | 3회 재시도 (5초 간격, 타임아웃 5분), 전체 실패 시 **발행 차단** |
| AI 응답 JSON 파싱 실패 | `{`~`}` 추출, 코드블록 제거 후 재시도, 최종 실패 시 **발행 차단** |
| AI 분석 품질 미달 | 기본 제목("시장 리포트") 반환 시 **발행 차단** |
| 같은 리포트 중복 발행 | WordPress API로 오늘 동일 카테고리 발행 여부 확인, 중복 시 스킵 |
| 홈페이지 업데이트 실패 | 경고 출력 후 리포트 발행 계속 진행 |
| 마켓 캘린더 업데이트 실패 | 경고 출력 후 리포트 발행 계속 진행 |
| WordPress 발행 실패 | 에러 로그 출력, None 반환 |

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 변동률이 5일 기준 | `chartPreviousClose`가 range 시작 기준 | `closes[-2]` 사용 (이미 적용) |
| HTML 레이아웃 깨짐 | twentytwentyfive 테마 CSS override | 인라인 CSS + `!important` (이미 적용) |
| 카테고리 페이지 갱신 안됨 | Breeze 캐시 | WP Admin → Breeze → Purge All Cache |
| us_market TimeoutError | API 응답 지연 (분석 데이터 많음) | timeout 300초(5분) + 3회 재시도 (이미 적용) |
| 미국 시장 0.00% | 주말/휴장 | 정상 동작 (금요일 마감 기준 분석) |
| Windows 인코딩 에러 | cp949 기본 인코딩 | `PYTHONIOENCODING=utf-8` 환경변수 |
| Finnhub economic calendar 403 | Free tier 미지원 | 정적 JSON으로 대체 (이미 적용) |
| GitHub Actions 401 Unauthorized | API 키 오등록 | Secrets에서 키 값 재확인 |

## 변경 이력

- **2026-03-18**: 중복 발행 방지 + AI 품질 게이트
  - 로컬 파일(publish_log.jsonl) 중복 체크 → WordPress API 기반으로 교체
  - AI 분석 실패/품질 미달 시 발행 차단 (빈 리포트 발행 원천 방지)
  - AI API 타임아웃 180초 → 300초(5분) 확대
  - 장전 리포트 스케줄 07:57 → 06:50 (7시 발행 목표)
  - GitHub Actions workflow timeout 10분 → 15분

- **2026-03-16**: 종합 안정성 개선
  - AI 분석 3회 재시도 + 타임아웃 180초 확대
  - 파이프라인 전체 에러 핸들링 강화 (AI 실패 시에도 발행 가능)
  - 제목에서 `[카테고리 리포트]` 태그 완전 제거
  - 리포트 타입별 SEO excerpt 개선
  - publish_wp.py 테스트 코드 수정
  - 마켓 캘린더 모듈 추가 (Finnhub + 정적 경제지표 + 옵션만기)
  - Jakob Nielsen UX 원칙 적용 (홈, 아카이브, 싱글 포스트)
  - WordPress 카테고리 16개 설명 추가
  - 기존 51개 포스트 제목 태그 정리
  - GitHub Actions 워크플로우 구축 (daily + weekly)
  - 홈페이지 티커바/Market Pulse 실시간 연동

- **2026-03-16**: 초기 구축
  - 데이터 수집, AI 분석, HTML 생성, WordPress 발행 파이프라인
  - 달러인덱스 수집 추가
  - Breeze 캐시 퍼지 자동화
  - 카테고리별 포스트 배정 정상화

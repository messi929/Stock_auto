# StockBizView - AI 자동 주식 리포트 발행 시스템

> 한국/미국 시장 데이터를 수집하고, AI(Claude)가 세계적 투자 애널리스트 수준의 분석 리포트를 생성하여 WordPress에 자동 발행하는 시스템

## 시스템 구조

```
[Yahoo Finance API] → collect_data.py → latest_market_data.json
                                              ↓
                                        ai_analyst.py (Claude API)
                                              ↓
                                        generate_report.py (HTML 생성)
                                              ↓
                                        publish_wp.py (WordPress 발행 + 캐시 퍼지)
                                              ↓
                                        update_homepage.py (홈페이지 실시간 업데이트)

auto_publish.py ← 위 전체를 통합 실행하는 메인 파이프라인
```

## 파일 구조

```
Stock_auto/
├── collect_data.py        # 시장 데이터 수집 (Yahoo Finance v8 API)
├── ai_analyst.py          # AI 분석 생성 (Anthropic Claude API)
├── generate_report.py     # HTML 리포트 생성 (인라인 CSS, 다크 테마)
├── publish_wp.py          # WordPress REST API 발행 + Breeze 캐시 퍼지
├── update_homepage.py     # 홈페이지 티커바/Market Pulse 실시간 업데이트
├── auto_publish.py        # 통합 파이프라인 (수집→분석→생성→발행)
├── latest_market_data.json # 최근 수집 데이터 (자동 생성)
├── publish_log.jsonl      # 발행 이력 로그 (자동 생성)
├── .github/
│   └── workflows/
│       ├── daily_reports.yml   # 매일 장전/장후 리포트 (GitHub Actions)
│       └── weekly_reports.yml  # 주간 리포트 4종 (GitHub Actions)
└── README.md
```

## 리포트 종류 (6종)

| 타입 | 설명 | 발행 시간 (KST) | 카테고리 ID |
|------|------|-----------------|-------------|
| `pre_market` | 장전 리포트 | 매일 07:57 | 2 |
| `post_market` | 장후 리포트 | 매일 19:03 | 3 |
| `us_market` | 미국 시장 심층 분석 | 화/금 09:13 | 7 |
| `korea_market` | 한국 시장 심층 분석 | 월/목 19:33 | 6 |
| `stock_analysis` | 종목 분석 | 화/금 19:47 | 4 |
| `investment_strategy` | 투자 전략 | 수 09:07 | 5 |

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
```

### GitHub Actions 자동화

GitHub 리포지토리에 push하면 cron 스케줄에 따라 자동 실행됩니다.
수동 실행: Actions 탭 → 워크플로우 선택 → Run workflow

## 환경 변수 (Secrets)

### 필수

| 변수 | 설명 |
|------|------|
| `ANTHROPIC_API_KEY` | Claude API 키 |
| `WP_URL` | WordPress URL (`https://stockbizview.com`) |
| `WP_USER` | WordPress 사용자 이메일 |
| `WP_APP_PASSWORD` | WordPress Application Password |

### 선택 (Cloudways 캐시 자동 퍼지)

| 변수 | 설명 |
|------|------|
| `CLOUDWAYS_EMAIL` | Cloudways 계정 이메일 |
| `CLOUDWAYS_API_KEY` | Cloudways API 키 |
| `CLOUDWAYS_SERVER_ID` | Cloudways 서버 ID |
| `CLOUDWAYS_APP_ID` | Cloudways 앱 ID (현재: `6277778`) |

## 인프라

- **호스팅**: Cloudways (DigitalOcean)
- **CMS**: WordPress 6.x + twentytwentyfive 테마
- **캐시**: Breeze 플러그인 (TTL: 60분) + Object Cache Pro (Redis)
- **AI**: Anthropic Claude (claude-sonnet-4-6)
- **CI/CD**: GitHub Actions
- **도메인**: stockbizview.com
- **서버 IP**: 158.247.221.235

## 기술 구현 상세

### 데이터 수집 (`collect_data.py`)
- Yahoo Finance v8 Chart API (`query1.finance.yahoo.com/v8/finance/chart/`)
- 1일 변동률: `closes[-2]` 기준 (chartPreviousClose는 range 기준이라 부정확)
- User-Agent 헤더 필수

### AI 분석 (`ai_analyst.py`)
- 리포트 타입별 전용 프롬프트 (골드만삭스/모건스탠리/삼성증권 등 페르소나)
- JSON 형식 응답 → 파싱 (코드블록 제거, `{`~`}` 추출, fallback)
- max_tokens: 4000

### HTML 리포트 (`generate_report.py`)
- 완전 인라인 CSS (twentytwentyfive 테마 override 위해 `!important` 사용)
- 다크 테마 (#0d1117 배경)
- 반응형: metric cards, bar charts, 테이블
- AI 내러티브 섹션: 시황분석, 섹터분석, 리스크, 전략, 전망

### WordPress 발행 (`publish_wp.py`)
- REST API v2 (`/wp-json/wp/v2/posts`)
- Basic Auth (Application Password)
- 카테고리 자동 배정, 태그 생성/검색
- 발행 후 Breeze 캐시 퍼지

### 홈페이지 업데이트 (`update_homepage.py`)
- WordPress FSE 템플릿 API로 home 템플릿 직접 수정
- 티커바: KOSPI, KOSDAQ, S&P 500, NASDAQ, USD/KRW, BTC
- Market Pulse: VIX, WTI, 금, US 10Y, 달러인덱스, 비트코인
- 리포트 발행 시마다 자동 갱신

### 파이프라인 (`auto_publish.py`)
```
Step 1/5: 시장 데이터 수집 (Yahoo Finance)
Step 2/5: 홈페이지 실시간 업데이트 (티커바 + Market Pulse)
Step 3/5: AI 애널리스트 분석 생성 (Claude API)
Step 4/5: HTML 리포트 생성
Step 5/5: WordPress 발행 + 캐시 퍼지
```

## WordPress 카테고리 구조

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

## 트러블슈팅

### 자주 발생하는 문제

| 증상 | 원인 | 해결 |
|------|------|------|
| 변동률이 5일 기준 | `chartPreviousClose`가 range 시작 기준 | `closes[-2]` 사용 (이미 적용) |
| HTML 레이아웃 깨짐 | twentytwentyfive 테마 CSS override | 인라인 CSS + `!important` (이미 적용) |
| 카테고리 페이지 갱신 안됨 | Breeze 캐시 | WP Admin → Breeze → Purge All Cache |
| AI 분석 JSON 파싱 실패 | 응답에 코드블록/텍스트 포함 | `{`~`}` 추출 + fallback (이미 적용) |
| 미국 시장 0.00% | 주말/휴장 | 정상 동작 (금요일 마감 기준 분석) |
| Windows 인코딩 에러 | cp949 기본 인코딩 | `PYTHONIOENCODING=utf-8` 환경변수 |

## 변경 이력

- **2026-03-16**: 초기 구축 완료
  - 데이터 수집, AI 분석, HTML 생성, WordPress 발행 파이프라인
  - GitHub Actions 자동화 (daily + weekly)
  - 홈페이지 티커바/Market Pulse 실시간 연동
  - 달러인덱스 수집 추가
  - Breeze 캐시 퍼지 자동화
  - 카테고리별 포스트 배정 정상화

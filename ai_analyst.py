"""
StockBizView - AI 애널리스트 모듈
Anthropic Claude API로 세계적 투자 애널리스트 수준의 분석 생성
"""

import json
import os
import urllib.request

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-6"
API_URL = "https://api.anthropic.com/v1/messages"

# === 공통 작성 규칙 ===
COMMON_RULES = """
## 공통 작성 규칙
- 한국어로 작성하되, 글로벌 IB 리서치 수준의 전문성과 깊이를 유지
- 데이터에 없는 뉴스/이벤트는 추측하지 말 것 — 수치 기반 분석만
- 미국 시장 변동률이 0.00%이면 "주말 휴장"으로 처리하고 금요일 마감 기준으로 분석
- 모든 주장에는 반드시 구체적 수치를 인용 (예: "KOSPI가 5,640.48(+1.63%)로...")
- 단순 수치 나열이 아닌, 수치 간의 인과관계와 상관관계를 분석하여 서술
- 각 단락은 최소 3~5문장으로 깊이 있게 작성 (한두 문장의 피상적 분석 금지)
- 전문 용어와 투자 프레임워크를 적극 활용 (예: PER, PBR, 이동평균선, 볼린저밴드, 상대강도 등)
- 냉철하고 객관적인 톤이지만, 확신이 있는 부분에서는 명확한 방향성을 제시

## 분석 품질 기준
- executive_summary: 핵심 3줄 요약으로 바쁜 투자자가 30초 만에 핵심 파악 가능하도록
- market_overview: 각 단락마다 "현상 → 원인 → 시사점" 3단 구조로 깊이 분석
- sector_analysis: 종목별 수치를 섹터 맥락과 글로벌 peer 비교 관점에서 해석
- technical_levels: 구체적 지지선/저항선 수치와 근거를 제시
- money_flow: 수급 데이터를 해석하여 향후 자금흐름 방향을 추론
- key_numbers: 오늘 반드시 기억해야 할 핵심 숫자 3~5개 선정 및 의미 해석
- risk_factors: 단순 나열이 아닌 "발생 확률 × 영향도" 관점의 우선순위 분석
- strategy: "어떤 조건에서 → 무엇을 → 언제까지" 형태의 실행 가능한 전략
- tomorrow_outlook: 시나리오별(베이스/불/베어) 전망 제시
"""

REPORT_PROMPTS = {
    "pre_market": f"""당신은 골드만삭스/모건스탠리 수석 글로벌 전략가입니다. 아래 시장 데이터를 바탕으로 세계 최고 수준의 장전 브리핑 리포트를 작성하세요.
{COMMON_RULES}

## 장전 리포트 특화 규칙
- 전일 미국 시장의 움직임이 한국 시장에 미칠 영향을 다층적으로 분석
- 환율/원자재의 변동이 한국 수출기업과 내수기업에 미치는 차별적 영향 분석
- 글로벌 자금흐름과 한국 시장 유입/유출 가능성을 연결
- 기술적 분석: 전일 종가 기준 주요 지수의 이동평균선 위치와 추세 판단

## 출력 형식 (JSON)
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만 출력:
{{
    "title": "강렬한 헤드라인 30~40자 (핵심 수치와 방향성 포함)",
    "seo_title": "구글 검색 최적화 제목 (규칙: ① 'X월 X일 증시 전망' 또는 'X월 X일 코스피 전망'으로 시작 ② 핵심 키워드 2개 포함(예: 반도체 강세, 원화 약세) ③ 40~50자 ④ 문학적 표현 금지, 검색어 중심 ⑤ 예시: '3월 21일 증시 전망 | 반도체 급등·원화 약세 장전 분석')",
    "headline": "시장 핵심 동향을 담은 임팩트 있는 한줄 요약 (60자 내외, 구체적 수치 포함)",
    "executive_summary": ["핵심 포인트 1 (가장 중요한 시장 변화)", "핵심 포인트 2 (투자자 액션 포인트)", "핵심 포인트 3 (리스크/기회 요인)"],
    "market_overview": ["전일 미국 3대 지수 종합 분석 — 상승/하락 원인, 거래량, 섹터별 차별화 (4~5문장)", "글로벌 매크로 환경 — 금리/달러/유동성/자금흐름 분석 (4~5문장)", "환율/원자재가 한국 시장에 미칠 구체적 영향 경로 분석 (4~5문장)"],
    "sector_analysis": ["반도체/IT 섹터 심층 분석 — 글로벌 반도체 사이클, 한국 기업 위치, 밸류에이션 (4~5문장)", "기타 주도 섹터 분석 — 자동차/바이오/금융/2차전지 등 (4~5문장)", "섹터 로테이션 흐름과 오늘 주목할 테마 (3~4문장)"],
    "technical_levels": ["KOSPI 기술적 분석 — 지지선/저항선, 이동평균선, 추세 판단 (3~4문장)", "KOSDAQ 기술적 분석 (3~4문장)", "원/달러 기술적 분석 — 핵심 레벨과 방향성 (2~3문장)"],
    "money_flow": ["외국인 자금흐름 전망 — 환율/글로벌 유동성/ETF 자금 기반 분석 (3~4문장)", "기관/개인 수급 예상과 프로그램 매매 영향 (2~3문장)"],
    "key_numbers": ["오늘의 핵심 숫자 1: 수치 + 의미 해석", "핵심 숫자 2: 수치 + 의미 해석", "핵심 숫자 3: 수치 + 의미 해석"],
    "risk_factors": ["리스크 1: 발생 시나리오, 임계점, 영향도 (3~4문장)", "리스크 2: 동일 구조 (3~4문장)"],
    "strategy": ["공격적 전략 — 대상 종목/섹터, 진입 조건, 목표가, 손절 기준 (3~4문장)", "균형 전략 — 포트폴리오 비중 조절 방안 (3~4문장)", "방어적 전략 — 리스크 헤지 방법, 현금 비중 (2~3문장)"],
    "tomorrow_outlook": ["베이스 시나리오(확률 60%): 예상 흐름과 KOSPI 밴드 (3~4문장)", "불 시나리오(확률 25%): 상방 트리거와 예상 범위 (2~3문장)", "베어 시나리오(확률 15%): 하방 리스크와 대응 (2~3문장)", "핵심 모니터링 포인트 3가지"]
}}""",

    "post_market": f"""당신은 삼성증권/미래에셋 리서치센터 수석 애널리스트입니다. 아래 시장 데이터를 바탕으로 기관 투자자에게 배포하는 수준의 장후 리포트를 작성하세요.
{COMMON_RULES}

## 장후 리포트 특화 규칙
- 오늘 한국 시장(KOSPI/KOSDAQ) 실제 마감 데이터 중심 분석
- 미국 시장은 아직 개장 전이므로 미국 개별 종목(Mag7 등) 데이터는 제공되지 않음. 전일 미국 시장 영향은 지수 데이터로만 언급
- 상승/하락 종목의 원인을 섹터 맥락, 수급 구조, 글로벌 peer 비교로 다층 해석
- 장중 고저점과 종가의 관계에서 수급 강도를 판단
- 내일 장에 영향을 미칠 글로벌 이벤트 사전 분석

## 출력 형식 (JSON)
반드시 아래 JSON 형식으로만 응답하세요:
{{
    "title": "강렬한 헤드라인 30~40자",
    "seo_title": "구글 검색 최적화 제목 (규칙: ① 'X월 X일 코스피 +/-X.XX% 마감'으로 시작 ② '증시 장후 분석' 키워드 필수 ③ 40~50자 ④ 예시: '3월 20일 코스피 -2.43% 마감 | 증시 장후 분석')",
    "headline": "오늘 한국 시장 핵심 동향 한줄 요약 (60자 내외)",
    "executive_summary": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
    "market_overview": ["KOSPI/KOSDAQ 장 마감 종합 — 시가/고가/저가/종가 흐름, 거래대금, 장중 변곡점 분석 (5~6문장)", "수급 분석 — 외국인/기관/개인 매매 동향, 프로그램 매매 영향, 업종별 수급 차별화 (4~5문장)", "환율/원자재/글로벌 시장 연동 분석 — 원/달러 움직임과 한국 시장 상관관계 (4~5문장)"],
    "sector_analysis": ["강세 섹터/종목 심층 분석 — 상승 원인, 지속 가능성, 밸류에이션 레벨 (5~6문장)", "약세 섹터/종목 심층 분석 — 하락 원인, 반등 조건, 손절 기준 (4~5문장)", "대형주 vs 중소형주 차별화와 시장 breadth 분석 (3~4문장)"],
    "technical_levels": ["KOSPI 기술적 위치 — 종가 기준 지지/저항, 캔들 패턴, 거래량 시그널 (3~4문장)", "KOSDAQ 기술적 분석 (3~4문장)"],
    "money_flow": ["오늘 수급 결산 — 외국인/기관 순매수 상위 종목과 의미 (3~4문장)", "프로그램 매매/ETF 자금 흐름 분석 (2~3문장)"],
    "key_numbers": ["오늘의 핵심 숫자 1", "핵심 숫자 2", "핵심 숫자 3"],
    "risk_factors": ["구체적 리스크 1 — 임계점과 영향 경로 (3~4문장)", "리스크 2 (3~4문장)"],
    "strategy": ["단기 트레이딩 전략 — 내일 장 대응 (3~4문장)", "스윙 전략 — 2~5일 관점 포지셔닝 (3~4문장)", "중기 포지셔닝 — 포트폴리오 조정 방안 (3~4문장)"],
    "tomorrow_outlook": ["베이스 시나리오와 KOSPI 예상 밴드 (3~4문장)", "상방/하방 트리거와 시나리오별 대응 (3~4문장)", "핵심 모니터링 포인트 — 글로벌 이벤트, 수급 변수, 기술적 레벨 (3~4문장)"]
}}""",

    "us_market": f"""당신은 월가 최고 투자 전략가입니다. 아래 데이터로 미국 시장 심층 분석을 작성하세요.
{COMMON_RULES}

## 미국 시장 리포트 특화 규칙
- S&P 500/NASDAQ/다우 각각의 움직임을 개별 분석하고 차이점 해석
- Mag7 개별 종목을 사업부문별, 밸류에이션별로 세분화 분석
- 연준 정책과 금리 경로가 각 섹터에 미치는 차별적 영향 분석
- 한국 투자자 관점에서의 실행 가능한 전략 제시

## 출력 형식 (JSON)
{{
    "title": "미국 시장 심층 분석 헤드라인 30~40자",
    "seo_title": "구글 검색 최적화 제목 (규칙: ① 'X월 X일 미국 증시'로 시작 ② 나스닥/S&P500 등락 키워드 포함 ③ 40~50자 ④ 예시: '3월 20일 미국 증시 | 나스닥 -0.5% S&P500 보합 분석')",
    "headline": "월가 핵심 동향 한줄 요약 (60자 내외)",
    "executive_summary": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
    "market_overview": ["3대 지수 종합 분석 — 지수별 차별화 원인, 거래량, 시장 breadth (5~6문장)", "연준/금리/달러 — 통화정책 경로와 시장 기대 괴리 분석 (4~5문장)", "매크로 지표 해석 — 고용/소비/제조업/인플레이션 연결 (4~5문장)"],
    "sector_analysis": ["Mag7 개별 심층 분석 — 각 종목 실적/밸류에이션/모멘텀 (6~8문장)", "11개 GICS 섹터 로테이션 분석 — 자금 이동 방향과 의미 (4~5문장)", "주목 ETF/테마 — 구체적 티커와 투자 근거 (3~4문장)"],
    "technical_levels": ["S&P 500 기술적 분석 — 주요 레벨, 추세, 패턴 (3~4문장)", "NASDAQ 기술적 분석 (3~4문장)"],
    "money_flow": ["기관 자금흐름 — ETF 유입/유출, 옵션 포지셔닝 (3~4문장)", "해외 자금흐름과 달러 상관관계 (2~3문장)"],
    "key_numbers": ["핵심 숫자 1", "핵심 숫자 2", "핵심 숫자 3"],
    "risk_factors": ["지정학 리스크 — 구체적 시나리오와 영향 (3~4문장)", "금리/인플레 리스크 (3~4문장)", "시스템/유동성 리스크 (2~3문장)"],
    "strategy": ["미국 직접투자 전략 — 종목/ETF 구체적 추천 (4~5문장)", "한국 투자자 관점 — 환헤지, ADR, 연동 종목 활용법 (3~4문장)", "리스크 관리 — 포지션 사이징, 헤지 전략 (3~4문장)"],
    "tomorrow_outlook": ["주간 핵심 이벤트 캘린더와 예상 영향 (3~4문장)", "시나리오별 전망과 확률 평가 (3~4문장)", "핵심 모니터링 포인트 (2~3문장)"]
}}""",

    "stock_analysis": f"""당신은 증권사 리서치센터 기업분석 수석입니다. 아래 데이터에서 가장 주목할 종목 3-5개를 선정하여 심층 분석하세요.
{COMMON_RULES}

## 종목 분석 특화 규칙
- 등락률 상위/하위에서 흥미로운 스토리가 있는 종목 선정
- 각 종목을 "사업 모델 → 실적 모멘텀 → 밸류에이션 → 기술적 위치 → 투자의견" 순서로 분석
- 종목 간 상관관계와 포트폴리오 관점의 조합 제안
- 구체적인 매수/매도 가격대와 근거 제시

## 출력 형식 (JSON)
{{
    "title": "주목 종목 테마 헤드라인 30~40자",
    "seo_title": "구글 검색 최적화 제목 (규칙: ① 'X월 X일' + 종목명으로 시작 ② '주가 전망' 또는 '종목 분석' 키워드 필수 ③ 40~50자 ④ 예시: '3월 20일 삼성전자·SK하이닉스 주가 전망 | 반도체 종목 분석')",
    "headline": "오늘의 종목 분석 핵심 (60자 내외)",
    "executive_summary": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
    "market_overview": ["종목 선정 배경 — 시장 맥락과 테마 연결 (4~5문장)", "섹터 환경과 수급 구조가 선정 종목에 미치는 영향 (3~4문장)"],
    "sector_analysis": ["종목1: 주가동향, 사업모델 강점/약점, 실적 전망, 밸류에이션(PER/PBR), 기술적 지지/저항, 동종업계 비교 (6~8문장)", "종목2: 동일 구조 (6~8문장)", "종목3: 동일 구조 (6~8문장)"],
    "technical_levels": ["선정 종목별 핵심 기술적 레벨 — 매수/매도 시그널 (각 2~3문장)"],
    "money_flow": ["선정 종목 수급 동향 — 외국인/기관 매매 패턴과 의미 (3~4문장)"],
    "key_numbers": ["핵심 숫자 1", "핵심 숫자 2", "핵심 숫자 3"],
    "risk_factors": ["개별 종목 고유 리스크 (3~4문장)", "섹터/매크로 공통 리스크 (3~4문장)"],
    "strategy": ["종목별 매수/매도/관망 의견과 구체적 근거 (4~5문장)", "진입 가격, 목표가, 손절가 제시 (3~4문장)", "포트폴리오 조합과 비중 제안 (3~4문장)"],
    "tomorrow_outlook": ["단기 촉매 이벤트와 예상 주가 반응 (3~4문장)", "중기 모멘텀과 구조적 성장 스토리 (2~3문장)"]
}}""",

    "investment_strategy": f"""당신은 글로벌 자산운용사 CIO(Chief Investment Officer)입니다. 주간 투자 전략 리포트를 작성하세요.
{COMMON_RULES}

## 투자 전략 특화 규칙
- CIO 레터 톤: 거시적 관점에서 명확한 방향성과 구체적 비중 제시
- 주식/채권/현금/대체자산의 구체적 비중을 % 단위로 제안
- 지역별(한국/미국/유럽/아시아), 섹터별 over/underweight 제시
- 3가지 리스크 시나리오(베이스/불/베어)별 대응 전략 수립

## 출력 형식 (JSON)
{{
    "title": "주간 투자 전략 헤드라인 30~40자",
    "seo_title": "구글 검색 최적화 제목 (규칙: ① 'X월 N주차 투자 전략'으로 시작 ② '포트폴리오' 또는 '자산배분' 키워드 포함 ③ 40~50자 ④ 예시: '3월 3주차 투자 전략 | 방어주 비중 확대 포트폴리오')",
    "headline": "이번 주 투자 전략 핵심 (60자 내외)",
    "executive_summary": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
    "market_overview": ["글로벌 매크로 환경 점검 — 성장/인플레/유동성 3축 분석 (5~6문장)", "주요국 통화정책 방향과 시장 함의 (4~5문장)", "글로벌 자금 흐름 — 신흥국/선진국, 주식/채권 간 이동 (4~5문장)"],
    "sector_analysis": ["자산배분 전략 — 주식/채권/현금/대체자산 구체적 비중(%) (4~5문장)", "지역별 전략 — 한국/미국/유럽/중국 비중과 근거 (4~5문장)", "섹터 로테이션 — over/underweight 섹터와 구체적 ETF/종목 (4~5문장)"],
    "technical_levels": ["글로벌 주요 지수 기술적 위치와 추세 판단 (3~4문장)", "한국 시장 기술적 분석 (3~4문장)"],
    "money_flow": ["글로벌 펀드 플로우 — 지역별/자산별 자금 이동 (3~4문장)", "한국 시장 수급 전망 (2~3문장)"],
    "key_numbers": ["핵심 숫자 1", "핵심 숫자 2", "핵심 숫자 3"],
    "risk_factors": ["핵심 리스크 시나리오 — 확률과 영향도 (3~4문장)", "테일 리스크 — 낮은 확률이지만 고영향 (3~4문장)", "헤지 전략 — 구체적 수단과 비용 (3~4문장)"],
    "strategy": ["공격적 포트폴리오(성장 추구) — 구체적 비중과 종목 (4~5문장)", "균형 포트폴리오 — 위험 조정 수익 극대화 (4~5문장)", "방어적 포트폴리오 — 자산 보전 우선 (3~4문장)", "핵심 트레이드 아이디어 — 이번 주 베스트 트레이드 (3~4문장)"],
    "tomorrow_outlook": ["주간 경제 캘린더 — 핵심 이벤트와 예상 영향 (3~4문장)", "시나리오별 주간 전망 — 베이스/불/베어 (3~4문장)", "핵심 모니터링 포인트 (2~3문장)"]
}}""",

    "korea_market": f"""당신은 한국 증권사 리서치센터장입니다. 한국 시장 심층 분석을 작성하세요.
{COMMON_RULES}

## 한국 시장 특화 규칙
- KOSPI/KOSDAQ 중심의 심층 분석, 수급 데이터 중점 해석
- 업종별/시가총액별 차별화된 움직임과 원인 분석
- 외국인/기관의 매매 패턴에서 향후 방향성 추론
- 한국 시장 고유의 리스크(환율, 정책, 북한 등) 평가

## 출력 형식 (JSON)
{{
    "title": "한국 시장 심층 분석 헤드라인 30~40자",
    "seo_title": "구글 검색 최적화 제목 (규칙: ① 'X월 X일 코스피·코스닥 분석'으로 시작 ② 핵심 테마 키워드 포함 ③ 40~50자 ④ 예시: '3월 20일 코스피·코스닥 분석 | 외국인 매수 전환 섹터 전략')",
    "headline": "한국 시장 핵심 동향 요약 (60자 내외)",
    "executive_summary": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
    "market_overview": ["KOSPI/KOSDAQ 종합 — 지수 기술적 위치, 시장 breadth, 거래대금 추이 (5~6문장)", "수급 심층 분석 — 외국인/기관/개인 3주체 매매 패턴, 프로그램 영향, 공매도 (5~6문장)", "환율과 시장 — 원/달러 움직임이 업종별로 미치는 차별적 영향 (4~5문장)"],
    "sector_analysis": ["강세 업종 TOP3 — 상승 원인, 지속 가능성, 핵심 종목 (5~6문장)", "약세 업종 — 하락 원인, 반등 조건 (4~5문장)", "대형주 vs 중소형주 — 시장 스타일 진단 (3~4문장)", "테마별 동향 — AI/2차전지/바이오/방산 등 (3~4문장)"],
    "technical_levels": ["KOSPI 기술적 심층 — 이동평균선, 볼린저밴드, RSI, MACD (4~5문장)", "KOSDAQ 기술적 분석 (3~4문장)", "원/달러 기술적 분석 (2~3문장)"],
    "money_flow": ["외국인 매매 패턴 분석과 향후 전망 (4~5문장)", "기관 매매 — 연기금/투신/보험 주체별 분석 (3~4문장)", "개인/신용잔고/공매도 동향 (2~3문장)"],
    "key_numbers": ["핵심 숫자 1", "핵심 숫자 2", "핵심 숫자 3"],
    "risk_factors": ["환율/수출/중국 리스크 — 영향 경로와 임계점 (3~4문장)", "정책/정치 리스크 (3~4문장)", "글로벌 연동 리스크 — 미국/중국/유럽 전이 경로 (3~4문장)"],
    "strategy": ["기술적 지지/저항 기반 트레이딩 전략 (4~5문장)", "섹터 비중확대/축소 구체적 제안 (4~5문장)", "KOSDAQ 유망 종목군과 투자 근거 (3~4문장)"],
    "tomorrow_outlook": ["향후 2~3일 시나리오별 전망 (3~4문장)", "핵심 모니터링 포인트 — 수급/이벤트/기술적 레벨 (3~4문장)", "주간 전략 방향성 (2~3문장)"]
}}""",

    "weekly_recap_kr": f"""당신은 삼성증권 리서치센터장 겸 한국투자증권 CIO입니다. 이번 한 주간의 한국 시장을 종합적으로 리뷰하는 **주간 리포트**를 작성하세요.
{COMMON_RULES}

## 주간 한국 시장 리포트 특화 규칙
- 이번 한 주(월~금) 전체의 흐름을 조감도 관점에서 분석 — 단일 날짜가 아닌 주간 추세 중심
- 제공된 데이터의 daily 배열에서 요일별 흐름(시가→종가 변화)을 읽고 주간 내 변곡점 식별
- 주간 시가(월요일 시가) 대비 주간 종가(금요일 종가) 기준으로 주간 등락률 계산
- 한 주간 외국인/기관/개인 누적 수급 흐름과 방향성 추론
- 업종별 주간 성과 차별화: 승자/패자 업종 선정 및 다음 주 지속 가능성 평가
- KOSPI/KOSDAQ의 주간 고점/저점과 해당 시점의 촉매(catalyst) 분석
- 환율(원/달러) 주간 흐름이 수출주/내수주에 미친 차별적 영향
- 다음 주 핵심 이벤트 캘린더(FOMC, 옵션만기, 실적발표 등)와 예상 영향
- 글로벌 시장(미국/중국/유럽) 주간 동향이 한국 시장에 미치는 영향 연결

## 출력 형식 (JSON)
{{
    "title": "이번 주 한국 시장 주간 리뷰 헤드라인 30~40자 (주간 핵심 테마와 방향성 포함)",
    "seo_title": "구글 검색 최적화 제목 (규칙: ① 'X월 N주차 코스피 주간 리뷰'로 시작 ② 핵심 테마 키워드 포함 ③ 40~50자 ④ 예시: '3월 3주차 코스피 주간 리뷰 | 외국인 매수 전환·반도체 강세')",
    "headline": "이번 주 한국 시장 핵심 동향 한줄 요약 (60자 내외, 주간 등락률 포함)",
    "executive_summary": ["이번 주 가장 중요한 시장 변화 (주간 KOSPI/KOSDAQ 등락률 필수 포함)", "주간 수급/섹터 핵심 트렌드", "다음 주를 위한 핵심 시사점"],
    "market_overview": ["주간 KOSPI/KOSDAQ 종합 — 월~금 요일별 흐름, 주간 시가→종가 변화, 주간 고저점과 변곡점 분석, 거래대금 추이 (6~8문장)", "주간 수급 종합 — 외국인/기관/개인 5일간 누적 매매 동향, 프로그램 매매, 주간 수급 반전/지속 판단 (5~6문장)", "환율/원자재/글로벌 연동 — 원/달러 주간 흐름, WTI/금/BTC 변동이 한국 시장에 미친 영향 (5~6문장)"],
    "sector_analysis": ["주간 강세 업종 TOP3 — 주간 상승률, 상승 배경, 주도 종목, 다음 주 지속 가능성 (6~7문장)", "주간 약세 업종 — 주간 하락률, 하락 원인, 반등 조건과 시점 예상 (5~6문장)", "주간 테마 분석 — AI/반도체/2차전지/바이오/방산/금융 등 주간 흐름과 다음 주 전망 (5~6문장)", "대형주 vs 중소형주 — 주간 스타일 분석, KOSPI200 vs KOSDAQ150 차별화 (3~4문장)"],
    "technical_levels": ["KOSPI 주간 기술적 분석 — 주봉 기준 이동평균선(5주/20주/60주), 주간 캔들 패턴, RSI/MACD 주간 시그널, 다음 주 지지/저항선 (5~6문장)", "KOSDAQ 주간 기술적 분석 — 동일 구조 (4~5문장)", "원/달러 주간 기술적 분석 — 주간 추세와 다음 주 예상 밴드 (3~4문장)"],
    "money_flow": ["외국인 주간 누적 매매 분석 — 순매수/순매도 업종별 패턴, 선물/현물 연계, 향후 방향성 (5~6문장)", "기관 주간 매매 — 연기금/투신/보험/사모 주체별 주간 행태와 의미 (4~5문장)", "개인/신용잔고/공매도 주간 동향 — 투자심리 진단 (3~4문장)"],
    "key_numbers": ["이번 주 핵심 숫자 1: 수치 + 주간 맥락에서의 의미 해석", "핵심 숫자 2", "핵심 숫자 3", "핵심 숫자 4", "핵심 숫자 5"],
    "risk_factors": ["다음 주 핵심 리스크 1 — 발생 시나리오, 임계점, KOSPI 영향 범위 (4~5문장)", "리스크 2 — 동일 구조 (4~5문장)", "테일 리스크 — 낮은 확률이지만 발생 시 고영향 이벤트 (3~4문장)"],
    "strategy": ["다음 주 공격적 전략 — 주목 섹터/종목, 진입 조건, 목표가, 손절 기준 (5~6문장)", "다음 주 균형 전략 — 포트폴리오 비중 조절, 업종 over/underweight (4~5문장)", "다음 주 방어적 전략 — 리스크 헤지, 현금 비중, 인버스 ETF 활용 (3~4문장)"],
    "tomorrow_outlook": ["다음 주 베이스 시나리오(확률 55%) — KOSPI 예상 밴드, 주간 흐름 예상, 핵심 촉매 (4~5문장)", "불 시나리오(확률 25%) — 상방 트리거, 돌파 시 목표 (3~4문장)", "베어 시나리오(확률 20%) — 하방 리스크, 지지선 이탈 시 대응 (3~4문장)", "다음 주 핵심 이벤트 캘린더 — 날짜별 주요 일정과 예상 시장 영향 (3~4문장)"]
}}""",

    "weekly_recap_us": f"""당신은 JP모건 수석 글로벌 전략가 겸 골드만삭스 CIO입니다. 이번 한 주간의 미국 시장을 종합적으로 리뷰하는 **주간 리포트**를 작성하세요.
{COMMON_RULES}

## 주간 미국 시장 리포트 특화 규칙
- 이번 한 주(월~금) 전체의 흐름을 조감도 관점에서 분석 — 단일 날짜가 아닌 주간 추세 중심
- 제공된 데이터의 daily 배열에서 요일별 흐름(시가→종가 변화)을 읽고 주간 내 변곡점 식별
- S&P 500/NASDAQ/다우 각각의 주간 흐름과 차별화 원인 분석
- Mag7 개별 종목의 주간 성과 분석 — 사업부문별, 밸류에이션별 세분화
- 주간 시가(월요일 시가) 대비 주간 종가(금요일 종가) 기준 주간 등락률 계산
- 연준 정책 경로, 금리, 달러, 유동성의 주간 변화와 시장 영향
- 11개 GICS 섹터별 주간 성과 순위와 로테이션 흐름
- 주간 옵션 시장 포지셔닝, VIX 흐름, 기관 자금 유입/유출
- 한국 투자자 관점에서의 시사점과 실행 가능한 전략
- 다음 주 핵심 이벤트(FOMC, 고용지표, 실적발표 등)와 예상 영향

## 출력 형식 (JSON)
{{
    "title": "이번 주 미국 시장 주간 리뷰 헤드라인 30~40자 (주간 핵심 테마와 방향성 포함)",
    "seo_title": "구글 검색 최적화 제목 (규칙: ① 'X월 N주차 미국 증시 주간 리뷰'로 시작 ② 나스닥/S&P500 키워드 포함 ③ 40~50자 ④ 예시: '3월 3주차 미국 증시 주간 리뷰 | 나스닥 반등·테크주 강세')",
    "headline": "이번 주 월가 핵심 동향 한줄 요약 (60자 내외, 주간 등락률 포함)",
    "executive_summary": ["이번 주 가장 중요한 시장 변화 (주간 3대 지수 등락률 필수 포함)", "주간 Mag7/섹터 핵심 트렌드", "다음 주를 위한 핵심 시사점"],
    "market_overview": ["3대 지수 주간 종합 — 월~금 요일별 흐름, 주간 시가→종가 변화, 지수별 차별화 원인, 거래량/breadth 변화 (6~8문장)", "연준/금리/달러 주간 동향 — 금리 기대 변화, 달러인덱스 흐름, 유동성 환경 변화 (5~6문장)", "매크로 지표 주간 종합 — 발표된 고용/소비/제조업/인플레이션 지표와 시장 반응 (5~6문장)"],
    "sector_analysis": ["Mag7 주간 개별 심층 분석 — 각 종목 주간 등락률, 주간 내 촉매, 밸류에이션 변화, 모멘텀 판단 (8~10문장)", "11개 GICS 섹터 주간 성과 순위 — 상위/하위 3개 섹터, 자금 이동 방향, 로테이션 의미 (5~6문장)", "주목 ETF/테마 — 주간 자금 유입 상위 ETF, 신규 테마, 구체적 티커와 투자 근거 (4~5문장)"],
    "technical_levels": ["S&P 500 주간 기술적 분석 — 주봉 기준 이동평균선, 주간 캔들 패턴, RSI/MACD, 다음 주 지지/저항 (5~6문장)", "NASDAQ 주간 기술적 분석 — 동일 구조 (4~5문장)", "다우존스/러셀2000 주간 기술적 분석 (3~4문장)"],
    "money_flow": ["기관 주간 자금흐름 — ETF 유입/유출 순위, 옵션 포지셔닝 변화, Put/Call 비율 추이 (5~6문장)", "해외 자금흐름 — 신흥국 vs 선진국 자금 이동, 달러 연동, 글로벌 펀드 플로우 (4~5문장)"],
    "key_numbers": ["이번 주 핵심 숫자 1: 수치 + 주간 맥락에서의 의미 해석", "핵심 숫자 2", "핵심 숫자 3", "핵심 숫자 4", "핵심 숫자 5"],
    "risk_factors": ["다음 주 지정학 리스크 — 구체적 시나리오와 시장 영향 경로 (4~5문장)", "금리/인플레 리스크 — 연준 경로 변경 가능성과 영향 (4~5문장)", "시스템/유동성 리스크 — 레버리지, 신용, 시장 구조 이슈 (3~4문장)"],
    "strategy": ["다음 주 미국 직접투자 전략 — 섹터별 over/underweight, 구체적 종목/ETF 추천, 진입 조건 (5~6문장)", "한국 투자자 관점 — 환헤지 전략, ADR, 연동 한국 종목, 원화 약세/강세 시나리오별 대응 (4~5문장)", "리스크 관리 — 포지션 사이징, VIX 활용 헤지, 현금 비중 (4~5문장)"],
    "tomorrow_outlook": ["다음 주 핵심 이벤트 캘린더 — 날짜별 주요 일정(FOMC/고용/실적/CPI 등)과 예상 시장 영향 (4~5문장)", "다음 주 시나리오별 전망 — 베이스(55%)/불(25%)/베어(20%) 확률과 예상 밴드 (4~5문장)", "핵심 모니터링 포인트 — 금리/달러/VIX/옵션 만기 (3~4문장)"]
}}""",
}


REQUIRED_SECTIONS = [
    "title", "headline", "executive_summary", "market_overview",
    "sector_analysis", "technical_levels", "money_flow",
    "key_numbers", "risk_factors", "strategy", "tomorrow_outlook",
]

# 최소 충족 기준: 이 섹션들이 비어있으면 품질 미달
CRITICAL_SECTIONS = [
    "executive_summary", "market_overview", "sector_analysis",
    "technical_levels", "money_flow", "key_numbers",
]


def _call_claude_api(payload):
    """Claude API 단일 호출 (재시도 포함)"""
    body = json.dumps(payload).encode("utf-8")

    for attempt in range(3):
        try:
            req = urllib.request.Request(API_URL, data=body, method="POST")
            req.add_header("x-api-key", API_KEY)
            req.add_header("anthropic-version", "2023-06-01")
            req.add_header("content-type", "application/json")
            with urllib.request.urlopen(req, timeout=300) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            return result["content"][0]["text"]
        except Exception as e:
            print(f"  ⚠️ API 호출 실패 (시도 {attempt+1}/3): {e}")
            if attempt < 2:
                import time
                time.sleep(5)

    return None


def _parse_json_response(text):
    """API 응답 텍스트에서 JSON 추출"""
    if not text:
        return None

    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0].strip()

    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"  ⚠️ JSON 파싱 실패")
        return None


def _find_missing_sections(analysis):
    """비어있는 필수 섹션 목록 반환"""
    missing = []
    for key in CRITICAL_SECTIONS:
        val = analysis.get(key)
        if not val or (isinstance(val, list) and len(val) == 0):
            missing.append(key)
    return missing


def _build_supplement_prompt(missing_sections, data_summary, report_type):
    """누락된 섹션만 보충 생성하는 프롬프트"""
    # 원본 프롬프트에서 해당 섹션의 형식 설명 추출
    original_prompt = REPORT_PROMPTS.get(report_type, REPORT_PROMPTS["post_market"])

    section_descriptions = {
        "executive_summary": '"executive_summary": ["핵심 포인트 1 (가장 중요한 시장 변화)", "핵심 포인트 2 (투자자 액션 포인트)", "핵심 포인트 3 (리스크/기회 요인)"]',
        "market_overview": '"market_overview": ["시황 분석 단락1 (4~5문장)", "시황 분석 단락2 (4~5문장)", "시황 분석 단락3 (4~5문장)"]',
        "sector_analysis": '"sector_analysis": ["섹터 분석 단락1 (4~5문장)", "섹터 분석 단락2 (4~5문장)", "섹터 분석 단락3 (3~4문장)"]',
        "technical_levels": '"technical_levels": ["KOSPI 기술적 분석 — 지지선/저항선, 이동평균선, 추세 판단 (3~4문장)", "KOSDAQ 기술적 분석 (3~4문장)", "원/달러 기술적 분석 (2~3문장)"]',
        "money_flow": '"money_flow": ["외국인 자금흐름 전망 (3~4문장)", "기관/개인 수급 예상 (2~3문장)"]',
        "key_numbers": '"key_numbers": ["오늘의 핵심 숫자 1: 수치 + 의미 해석", "핵심 숫자 2: 수치 + 의미 해석", "핵심 숫자 3: 수치 + 의미 해석"]',
    }

    fields = ",\n    ".join(section_descriptions.get(s, f'"{s}": ["내용"]') for s in missing_sections)

    return f"""아래 시장 데이터를 바탕으로 누락된 분석 섹션을 보충 작성하세요.
{COMMON_RULES}

## 시장 데이터
{data_summary}

## 출력 형식 (JSON)
반드시 아래 JSON 형식으로만 응답하세요:
{{
    {fields}
}}"""


def generate_analysis(data_summary, report_type="post_market"):
    """Claude API로 애널리스트 분석 생성 (품질 검증 + 보충 재시도)"""
    system_prompt = REPORT_PROMPTS.get(report_type, REPORT_PROMPTS["post_market"])

    default_analysis = {
        "title": "시장 리포트",
        "headline": "",
        "executive_summary": [],
        "market_overview": [],
        "sector_analysis": [],
        "technical_levels": [],
        "money_flow": [],
        "key_numbers": [],
        "risk_factors": [],
        "strategy": [],
        "tomorrow_outlook": [],
    }

    # === 1차 호출: 전체 분석 생성 ===
    payload = {
        "model": MODEL,
        "max_tokens": 12000,
        "messages": [
            {"role": "user", "content": f"## 시장 데이터\n\n{data_summary}\n\n위 데이터를 분석하여 JSON으로 응답하세요. 반드시 모든 섹션(executive_summary, market_overview, sector_analysis, technical_levels, money_flow, key_numbers, risk_factors, strategy, tomorrow_outlook)을 빠짐없이 작성하세요. 각 섹션을 최대한 풍부하고 깊이 있게 작성하세요."}
        ],
        "system": system_prompt,
    }

    print("  📡 1차 API 호출 중...")
    text = _call_claude_api(payload)
    if not text:
        print("  ❌ API 호출 실패, 기본 분석 반환")
        return default_analysis

    analysis = _parse_json_response(text)
    if not analysis:
        print("  ❌ JSON 파싱 실패, 기본 분석 반환")
        return default_analysis

    # === 2차: 누락 섹션 검증 ===
    missing = _find_missing_sections(analysis)
    if not missing:
        section_count = sum(1 for k in CRITICAL_SECTIONS if analysis.get(k))
        print(f"  ✅ 분석 품질 검증 통과 ({section_count}/{len(CRITICAL_SECTIONS)} 섹션 완성)")
        return analysis

    print(f"  ⚠️ 누락 섹션 발견: {missing}")
    print(f"  📡 보충 API 호출 중...")

    # === 보충 호출: 누락된 섹션만 재생성 ===
    supplement_prompt = _build_supplement_prompt(missing, data_summary, report_type)
    supplement_payload = {
        "model": MODEL,
        "max_tokens": 6000,
        "messages": [
            {"role": "user", "content": supplement_prompt}
        ],
        "system": "당신은 세계적 투자 애널리스트입니다. 요청된 섹션을 깊이 있게 작성하세요. JSON으로만 응답하세요.",
    }

    supplement_text = _call_claude_api(supplement_payload)
    if supplement_text:
        supplement = _parse_json_response(supplement_text)
        if supplement:
            for key in missing:
                if supplement.get(key):
                    analysis[key] = supplement[key]
                    print(f"    ✅ {key} 보충 완료")

    # === 최종 검증 ===
    still_missing = _find_missing_sections(analysis)
    if still_missing:
        print(f"  ⚠️ 보충 후에도 누락: {still_missing}")
    else:
        print(f"  ✅ 모든 섹션 보충 완료")

    section_count = sum(1 for k in CRITICAL_SECTIONS if analysis.get(k))
    print(f"  📊 최종 품질: {section_count}/{len(CRITICAL_SECTIONS)} 필수 섹션 완성")

    return analysis


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from generate_report import load_data, build_data_summary

    report_type = sys.argv[1] if len(sys.argv) > 1 else "post_market"
    data = load_data()
    summary = build_data_summary(data, report_type)

    print(f"Generating {report_type} analysis...")
    analysis = generate_analysis(summary, report_type)
    print(json.dumps(analysis, ensure_ascii=False, indent=2))

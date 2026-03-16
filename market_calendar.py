"""
StockBizView - 마켓 캘린더 모듈
경제지표, 어닝, 한국 이벤트, 옵션만기 등을 수집하여
WordPress 마켓 캘린더 페이지에 자동 업데이트

사용법:
  python market_calendar.py          # 캘린더 업데이트
  python market_calendar.py --test   # 데이터만 확인
"""

import json
import os
import urllib.request
import base64
import datetime
import sys
import re

# ─── 설정 ───
WP_URL = os.environ.get("WP_URL", "https://stockbizview.com")
WP_USER = os.environ.get("WP_USER", "messi929@naver.com")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "s5cW A0gL vzNU AcgS exFC OL0r")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "d6rvbb9r01qgflm17770d6rvbb9r01qgflm1777g")
CALENDAR_PAGE_ID = 10


def _wp_request(endpoint, method="GET", data=None):
    url = f"{WP_URL}/wp-json/wp/v2/{endpoint}"
    auth = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    if data:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
    else:
        req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Basic {auth}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _finnhub_request(endpoint):
    url = f"https://finnhub.io/api/v1/{endpoint}&token={FINNHUB_API_KEY}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─── 2026 경제지표 일정 (미 연준/노동부/상무부 공식 일정) ───
ECONOMIC_EVENTS_2026 = [
    # FOMC 회의 (연준 공식 일정)
    {"date": "2026-01-27", "event": "FOMC 회의 시작", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-01-28", "event": "FOMC 금리 결정", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-03-17", "event": "FOMC 회의 시작", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-03-18", "event": "FOMC 금리 결정 + 점도표", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-05-05", "event": "FOMC 회의 시작", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-05-06", "event": "FOMC 금리 결정", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-06-16", "event": "FOMC 회의 시작", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-06-17", "event": "FOMC 금리 결정 + 점도표", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-07-28", "event": "FOMC 회의 시작", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-07-29", "event": "FOMC 금리 결정", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-09-15", "event": "FOMC 회의 시작", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-09-16", "event": "FOMC 금리 결정 + 점도표", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-11-03", "event": "FOMC 회의 시작", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-11-04", "event": "FOMC 금리 결정", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-12-15", "event": "FOMC 회의 시작", "country": "US", "impact": "high", "category": "central_bank"},
    {"date": "2026-12-16", "event": "FOMC 금리 결정 + 점도표", "country": "US", "impact": "high", "category": "central_bank"},

    # CPI (소비자물가지수) - 매월 둘째 주 화/수
    {"date": "2026-01-14", "event": "CPI 소비자물가지수 (12월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-02-11", "event": "CPI 소비자물가지수 (1월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-03-11", "event": "CPI 소비자물가지수 (2월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-04-14", "event": "CPI 소비자물가지수 (3월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-05-12", "event": "CPI 소비자물가지수 (4월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-06-10", "event": "CPI 소비자물가지수 (5월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-07-14", "event": "CPI 소비자물가지수 (6월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-08-12", "event": "CPI 소비자물가지수 (7월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-09-11", "event": "CPI 소비자물가지수 (8월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-10-13", "event": "CPI 소비자물가지수 (9월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-11-12", "event": "CPI 소비자물가지수 (10월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-12-10", "event": "CPI 소비자물가지수 (11월)", "country": "US", "impact": "high", "category": "economic"},

    # 고용보고서 (Non-Farm Payrolls) - 매월 첫째 금요일
    {"date": "2026-01-09", "event": "비농업 고용지표 (12월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-02-06", "event": "비농업 고용지표 (1월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-03-06", "event": "비농업 고용지표 (2월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-04-03", "event": "비농업 고용지표 (3월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-05-08", "event": "비농업 고용지표 (4월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-06-05", "event": "비농업 고용지표 (5월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-07-02", "event": "비농업 고용지표 (6월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-08-07", "event": "비농업 고용지표 (7월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-09-04", "event": "비농업 고용지표 (8월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-10-02", "event": "비농업 고용지표 (9월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-11-06", "event": "비농업 고용지표 (10월)", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-12-04", "event": "비농업 고용지표 (11월)", "country": "US", "impact": "high", "category": "economic"},

    # GDP (국내총생산) - 분기별
    {"date": "2026-01-29", "event": "GDP 4분기 속보치", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-02-26", "event": "GDP 4분기 수정치", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-03-26", "event": "GDP 4분기 확정치", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-04-29", "event": "GDP 1분기 속보치", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-05-28", "event": "GDP 1분기 수정치", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-06-25", "event": "GDP 1분기 확정치", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-07-29", "event": "GDP 2분기 속보치", "country": "US", "impact": "high", "category": "economic"},
    {"date": "2026-10-29", "event": "GDP 3분기 속보치", "country": "US", "impact": "high", "category": "economic"},

    # PPI (생산자물가) - 매월
    {"date": "2026-01-15", "event": "PPI 생산자물가 (12월)", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-02-13", "event": "PPI 생산자물가 (1월)", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-03-12", "event": "PPI 생산자물가 (2월)", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-04-09", "event": "PPI 생산자물가 (3월)", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-05-14", "event": "PPI 생산자물가 (4월)", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-06-11", "event": "PPI 생산자물가 (5월)", "country": "US", "impact": "medium", "category": "economic"},

    # ISM 제조업/서비스업 PMI - 매월 1~3일
    {"date": "2026-03-02", "event": "ISM 제조업 PMI (2월)", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-03-04", "event": "ISM 서비스업 PMI (2월)", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-04-01", "event": "ISM 제조업 PMI (3월)", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-04-03", "event": "ISM 서비스업 PMI (3월)", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-05-01", "event": "ISM 제조업 PMI (4월)", "country": "US", "impact": "medium", "category": "economic"},
    {"date": "2026-06-01", "event": "ISM 제조업 PMI (5월)", "country": "US", "impact": "medium", "category": "economic"},

    # 한국은행 금통위 (2026 일정)
    {"date": "2026-01-16", "event": "한국은행 금융통화위원회", "country": "KR", "impact": "high", "category": "central_bank"},
    {"date": "2026-02-27", "event": "한국은행 금융통화위원회", "country": "KR", "impact": "high", "category": "central_bank"},
    {"date": "2026-04-10", "event": "한국은행 금융통화위원회", "country": "KR", "impact": "high", "category": "central_bank"},
    {"date": "2026-05-22", "event": "한국은행 금융통화위원회", "country": "KR", "impact": "high", "category": "central_bank"},
    {"date": "2026-07-10", "event": "한국은행 금융통화위원회", "country": "KR", "impact": "high", "category": "central_bank"},
    {"date": "2026-08-21", "event": "한국은행 금융통화위원회", "country": "KR", "impact": "high", "category": "central_bank"},
    {"date": "2026-10-09", "event": "한국은행 금융통화위원회", "country": "KR", "impact": "high", "category": "central_bank"},
    {"date": "2026-11-20", "event": "한국은행 금융통화위원회", "country": "KR", "impact": "high", "category": "central_bank"},

    # 한국 GDP
    {"date": "2026-01-22", "event": "한국 GDP 4분기 속보치", "country": "KR", "impact": "high", "category": "economic"},
    {"date": "2026-04-23", "event": "한국 GDP 1분기 속보치", "country": "KR", "impact": "high", "category": "economic"},
    {"date": "2026-07-23", "event": "한국 GDP 2분기 속보치", "country": "KR", "impact": "high", "category": "economic"},
    {"date": "2026-10-22", "event": "한국 GDP 3분기 속보치", "country": "KR", "impact": "high", "category": "economic"},
]

# 미국 시장 휴일 2026
US_HOLIDAYS_2026 = [
    {"date": "2026-01-01", "event": "New Year's Day (미국 휴장)", "country": "US", "impact": "info", "category": "holiday"},
    {"date": "2026-01-19", "event": "Martin Luther King Jr. Day (미국 휴장)", "country": "US", "impact": "info", "category": "holiday"},
    {"date": "2026-02-16", "event": "Presidents' Day (미국 휴장)", "country": "US", "impact": "info", "category": "holiday"},
    {"date": "2026-04-03", "event": "Good Friday (미국 휴장)", "country": "US", "impact": "info", "category": "holiday"},
    {"date": "2026-05-25", "event": "Memorial Day (미국 휴장)", "country": "US", "impact": "info", "category": "holiday"},
    {"date": "2026-06-19", "event": "Juneteenth (미국 휴장)", "country": "US", "impact": "info", "category": "holiday"},
    {"date": "2026-07-03", "event": "Independence Day 대체휴일 (미국 휴장)", "country": "US", "impact": "info", "category": "holiday"},
    {"date": "2026-09-07", "event": "Labor Day (미국 휴장)", "country": "US", "impact": "info", "category": "holiday"},
    {"date": "2026-11-26", "event": "Thanksgiving Day (미국 휴장)", "country": "US", "impact": "info", "category": "holiday"},
    {"date": "2026-12-25", "event": "Christmas Day (미국 휴장)", "country": "US", "impact": "info", "category": "holiday"},
]

# 한국 시장 휴일 2026
KR_HOLIDAYS_2026 = [
    {"date": "2026-01-01", "event": "신정 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-01-27", "event": "설날 연휴 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-01-28", "event": "설날 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-01-29", "event": "설날 연휴 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-03-01", "event": "삼일절 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-05-05", "event": "어린이날 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-05-24", "event": "부처님오신날 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-06-06", "event": "현충일 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-08-15", "event": "광복절 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-09-24", "event": "추석 연휴 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-09-25", "event": "추석 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-09-26", "event": "추석 연휴 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-10-03", "event": "개천절 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-10-09", "event": "한글날 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
    {"date": "2026-12-25", "event": "크리스마스 (한국 휴장)", "country": "KR", "impact": "info", "category": "holiday"},
]


def get_options_expiry_dates(year=2026):
    """옵션 만기일 계산 (매월 셋째 금요일)"""
    events = []
    for month in range(1, 13):
        # 해당 월 1일의 요일 찾기
        first_day = datetime.date(year, month, 1)
        # 첫 번째 금요일 찾기
        days_until_friday = (4 - first_day.weekday()) % 7
        first_friday = first_day + datetime.timedelta(days=days_until_friday)
        # 셋째 금요일 = 첫 금요일 + 14일
        third_friday = first_friday + datetime.timedelta(days=14)

        label = "옵션 만기일"
        # 3, 6, 9, 12월은 쿼드러플 위칭
        if month in (3, 6, 9, 12):
            label = "쿼드러플 위칭데이 (옵션·선물 동시 만기)"
            impact = "high"
        else:
            impact = "medium"

        events.append({
            "date": third_friday.strftime("%Y-%m-%d"),
            "event": label,
            "country": "US",
            "impact": impact,
            "category": "options",
        })
    return events


def get_finnhub_earnings(weeks=3):
    """Finnhub에서 주요 어닝 일정 가져오기"""
    today = datetime.date.today()
    end = today + datetime.timedelta(weeks=weeks)

    # 관심 종목 (Mag7 + 주요 기업)
    watchlist = {
        "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet",
        "AMZN": "Amazon", "NVDA": "NVIDIA", "META": "Meta", "TSLA": "Tesla",
        "JPM": "JPMorgan", "BAC": "Bank of America", "GS": "Goldman Sachs",
        "WMT": "Walmart", "HD": "Home Depot", "NKE": "Nike",
        "DIS": "Disney", "NFLX": "Netflix", "CRM": "Salesforce",
        "AMD": "AMD", "INTC": "Intel", "QCOM": "Qualcomm",
        "V": "Visa", "MA": "Mastercard", "PYPL": "PayPal",
        "COST": "Costco", "TGT": "Target", "SBUX": "Starbucks",
        "BA": "Boeing", "CAT": "Caterpillar", "UNH": "UnitedHealth",
    }

    try:
        data = _finnhub_request(
            f"calendar/earnings?from={today}&to={end}"
        )
        earnings = data.get("earningsCalendar", [])

        events = []
        for e in earnings:
            symbol = e.get("symbol", "")
            if symbol in watchlist:
                eps_est = e.get("epsEstimate")
                eps_str = f" (EPS 예상: ${eps_est:.2f})" if eps_est else ""
                events.append({
                    "date": e["date"],
                    "event": f"{watchlist[symbol]} ({symbol}) 실적 발표{eps_str}",
                    "country": "US",
                    "impact": "high" if symbol in ("AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA") else "medium",
                    "category": "earnings",
                })

        print(f"  📊 Finnhub 어닝: {len(events)}건 (전체 {len(earnings)}건 중 주요 종목)")
        return events
    except Exception as e:
        print(f"  ⚠️ Finnhub 어닝 조회 실패: {e}")
        return []


def collect_all_events(weeks_ahead=4):
    """모든 이벤트를 수집하고 향후 N주 필터링"""
    today = datetime.date.today()
    start = today - datetime.timedelta(days=1)  # 어제부터 (진행 중 이벤트 포함)
    end = today + datetime.timedelta(weeks=weeks_ahead)

    all_events = []

    # 1) 경제지표 일정
    all_events.extend(ECONOMIC_EVENTS_2026)

    # 2) 옵션 만기일
    all_events.extend(get_options_expiry_dates(today.year))

    # 3) 미국/한국 휴일
    all_events.extend(US_HOLIDAYS_2026)
    all_events.extend(KR_HOLIDAYS_2026)

    # 4) Finnhub 어닝
    earnings = get_finnhub_earnings(weeks=weeks_ahead)
    all_events.extend(earnings)

    # 기간 필터링 + 날짜 정렬
    filtered = []
    for e in all_events:
        d = datetime.date.fromisoformat(e["date"])
        if start <= d <= end:
            filtered.append(e)

    filtered.sort(key=lambda x: x["date"])

    print(f"  📅 총 {len(filtered)}건 이벤트 (향후 {weeks_ahead}주)")
    return filtered


# ─── HTML 생성 ───

IMPACT_BADGE = {
    "high": '<span style="background:#f8514922;color:#f85149;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">HIGH</span>',
    "medium": '<span style="background:#d2992222;color:#d29922;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">MED</span>',
    "low": '<span style="background:#3fb95022;color:#3fb950;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">LOW</span>',
    "info": '<span style="background:#8b949e22;color:#8b949e;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">INFO</span>',
}

CATEGORY_ICON = {
    "central_bank": "🏛️",
    "economic": "📊",
    "earnings": "💰",
    "options": "📈",
    "holiday": "🏖️",
}

COUNTRY_FLAG = {
    "US": "🇺🇸",
    "KR": "🇰🇷",
}

DAY_NAMES_KR = {
    0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일",
}


def build_calendar_html(events):
    """마켓 캘린더 HTML 생성 (Nielsen UX 원칙 적용)"""
    now = datetime.datetime.now()
    today_str = datetime.date.today().isoformat()

    override_css = (
        "<style>"
        ".entry-content,.wp-block-post-content,.page-content,"
        ".site-main article .entry-content"
        "{max-width:100%!important;width:100%!important;padding-left:0!important;padding-right:0!important}"
        ".site-main,.wp-site-blocks>main{max-width:100%!important}"
        "</style>"
    )

    html = f"""{override_css}
<div style="background:#0d1117;color:#e6edf3;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;width:100%;max-width:1200px;margin:0 auto;padding:24px;box-sizing:border-box;">

  <!-- 캘린더 헤더 -->
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid #21262d;">
    <div>
      <h1 style="font-size:24px;font-weight:700;color:#e6edf3;margin:0 0 4px 0;">마켓 캘린더</h1>
      <p style="font-size:13px;color:#8b949e;margin:0;">경제지표 · 중앙은행 · 어닝 · 옵션만기 · 휴장일</p>
    </div>
    <div style="text-align:right;">
      <div style="font-size:11px;color:#8b949e;background:rgba(88,166,255,0.08);padding:6px 14px;border-radius:6px;border:1px solid rgba(88,166,255,0.15);">
        업데이트: {now.strftime("%Y.%m.%d %H:%M")} KST
      </div>
    </div>
  </div>

  <!-- 범례 -->
  <div style="display:flex;flex-wrap:wrap;gap:16px;margin-bottom:24px;padding:12px 16px;background:#161b22;border-radius:8px;border:1px solid #21262d;">
    <span style="font-size:12px;color:#8b949e;">범례:</span>
    <span style="font-size:12px;">🏛️ 중앙은행</span>
    <span style="font-size:12px;">📊 경제지표</span>
    <span style="font-size:12px;">💰 어닝</span>
    <span style="font-size:12px;">📈 옵션만기</span>
    <span style="font-size:12px;">🏖️ 휴장</span>
    <span style="font-size:12px;margin-left:auto;">{IMPACT_BADGE['high']} 고영향 {IMPACT_BADGE['medium']} 중영향 {IMPACT_BADGE['info']} 정보</span>
  </div>

"""

    # 주별로 그룹핑
    weeks = {}
    for e in events:
        d = datetime.date.fromisoformat(e["date"])
        # 해당 주의 월요일 기준
        week_start = d - datetime.timedelta(days=d.weekday())
        week_key = week_start.isoformat()
        if week_key not in weeks:
            weeks[week_key] = []
        weeks[week_key].append(e)

    for week_key in sorted(weeks.keys()):
        week_start = datetime.date.fromisoformat(week_key)
        week_end = week_start + datetime.timedelta(days=6)
        week_events = weeks[week_key]

        # 이번 주 하이라이트
        is_current_week = week_start <= datetime.date.today() <= week_end
        week_border = "border:1px solid rgba(88,166,255,0.3);background:#161b2280;" if is_current_week else "border:1px solid #21262d;background:#161b22;"
        week_label = ' <span style="background:#58a6ff;color:#0d1117;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;margin-left:8px;">THIS WEEK</span>' if is_current_week else ""

        html += f"""  <!-- 주간 섹션 -->
  <div style="{week_border}border-radius:12px;margin-bottom:16px;overflow:hidden;">
    <div style="padding:12px 20px;background:rgba(88,166,255,0.04);border-bottom:1px solid #21262d;">
      <span style="font-size:14px;font-weight:600;color:#e6edf3;">{week_start.strftime("%m/%d")} — {week_end.strftime("%m/%d")}</span>{week_label}
    </div>
    <div style="padding:0;">
"""

        # 날짜별 그룹핑
        day_groups = {}
        for e in week_events:
            if e["date"] not in day_groups:
                day_groups[e["date"]] = []
            day_groups[e["date"]].append(e)

        for date_str in sorted(day_groups.keys()):
            d = datetime.date.fromisoformat(date_str)
            day_name = DAY_NAMES_KR[d.weekday()]
            is_today = date_str == today_str
            today_bg = "background:rgba(88,166,255,0.06);" if is_today else ""
            today_dot = '<span style="display:inline-block;width:6px;height:6px;background:#58a6ff;border-radius:50%;margin-left:6px;vertical-align:middle;"></span>' if is_today else ""

            html += f"""      <div style="{today_bg}padding:10px 20px;border-bottom:1px solid #21262d0a;">
        <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:6px;">
          <span style="font-size:13px;font-weight:600;color:#e6edf3;min-width:80px;">{d.strftime("%m/%d")} ({day_name}){today_dot}</span>
        </div>
"""
            for e in day_groups[date_str]:
                icon = CATEGORY_ICON.get(e.get("category", ""), "📌")
                flag = COUNTRY_FLAG.get(e.get("country", ""), "")
                badge = IMPACT_BADGE.get(e.get("impact", "low"), IMPACT_BADGE["low"])

                html += f"""        <div style="display:flex;align-items:center;gap:10px;padding:4px 0 4px 92px;">
          <span style="font-size:14px;">{icon}</span>
          <span style="font-size:13px;color:#e6edf3;flex:1;">{flag} {e['event']}</span>
          {badge}
        </div>
"""
            html += "      </div>\n"

        html += "    </div>\n  </div>\n\n"

    # 면책조항
    html += """  <!-- 면책조항 -->
  <div style="text-align:center;padding:20px;border-top:1px solid #21262d;margin-top:8px;">
    <p style="font-size:11px;color:#484f58;margin:0;">
      일정은 변경될 수 있습니다. 정확한 일정은 각국 중앙은행 및 통계청 공식 발표를 확인하세요.<br>
      어닝 일정은 Finnhub API 기반으로 자동 업데이트됩니다.
    </p>
  </div>

</div>"""

    return html


def update_calendar_page(html_content):
    """WordPress 마켓 캘린더 페이지 업데이트"""
    print("\n📅 마켓 캘린더 페이지 업데이트 중...")

    try:
        _wp_request(f"pages/{CALENDAR_PAGE_ID}", method="POST", data={
            "content": html_content,
            "status": "publish",
        })
        print(f"  ✅ 마켓 캘린더 페이지 업데이트 완료 (ID: {CALENDAR_PAGE_ID})")
        print(f"  🔗 {WP_URL}/?page_id={CALENDAR_PAGE_ID}")
        return True
    except Exception as e:
        print(f"  ❌ 업데이트 실패: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  StockBizView 마켓 캘린더 Update")
    print("=" * 60)

    test_mode = "--test" in sys.argv

    # 이벤트 수집
    print("\n[1/2] 캘린더 이벤트 수집 중...")
    events = collect_all_events(weeks_ahead=4)

    # HTML 생성
    print("\n[2/2] 캘린더 HTML 생성 중...")
    html = build_calendar_html(events)
    print(f"  HTML 크기: {len(html):,} chars")

    if test_mode:
        print("\n[TEST MODE] WordPress 업데이트 건너뜀")
        # 로컬 미리보기 저장
        with open("calendar_preview.html", "w", encoding="utf-8") as f:
            f.write(f"<html><body style='background:#0d1117;margin:0;padding:20px;'>{html}</body></html>")
        print("  📄 calendar_preview.html 저장 완료")
    else:
        update_calendar_page(html)

    print("\n완료!")

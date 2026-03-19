"""
StockBizView - 시장 데이터 수집 모듈
Yahoo Finance v8 API를 사용하여 한국/미국 시장 데이터를 수집
"""

import json
import os
import urllib.request
import urllib.parse
import datetime
import sys
import io

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# 한국 시간대 (KST = UTC+9)
KST = datetime.timezone(datetime.timedelta(hours=9))

# === 심볼 정의 ===

INDICES = {
    "^KS11": "KOSPI",
    "^KQ11": "KOSDAQ",
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ",
    "^DJI": "다우존스",
}

COMMODITIES = {
    "KRW=X": "USD/KRW",
    "CL=F": "WTI 원유",
    "GC=F": "금",
    "BTC-USD": "비트코인",
    "^VIX": "VIX 공포지수",
    "^TNX": "미국 10년물 금리",
    "DX-Y.NYB": "달러인덱스",
}

KR_STOCKS = {
    "005930.KS": "삼성전자",
    "000660.KS": "SK하이닉스",
    "035420.KS": "NAVER",
    "035720.KS": "카카오",
    "005380.KS": "현대차",
    "068270.KS": "셀트리온",
    "006400.KS": "삼성SDI",
    "003670.KS": "포스코퓨처엠",
    "055550.KS": "신한지주",
    "105560.KS": "KB금융",
}

US_STOCKS = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "META": "Meta",
    "TSLA": "Tesla",
}


def fetch_chart(symbol, range_str="5d", interval="1d"):
    """Yahoo Finance v8 chart API에서 데이터 가져오기 (1일 변동률 기준)"""
    encoded = urllib.parse.quote(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?interval={interval}&range={range_str}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        result = data["chart"]["result"][0]
        meta = result["meta"]
        quote = result["indicators"]["quote"][0]
        timestamps = result.get("timestamp", [])

        price = meta.get("regularMarketPrice", 0)

        # 직전 거래일 종가를 daily 데이터에서 직접 추출 (1일 변동률)
        # Yahoo Finance는 미개장 당일에도 전일 종가를 복사한 bar를 반환하므로
        # 마지막 bar가 price와 동일하고 직전 bar와도 동일하면 복사본으로 간주하여 제거
        closes = [c for c in quote.get("close", []) if c is not None]
        if len(closes) >= 3:
            last = closes[-1]
            second_last = closes[-2]
            # 마지막 두 close가 사실상 동일하면 미개장 복사본 → 제거
            if last and second_last and abs(last - second_last) < 0.01:
                closes = closes[:-1]

        if len(closes) >= 2:
            prev_close = closes[-2]  # 직전 거래일 종가
        else:
            prev_close = meta.get("chartPreviousClose", price)

        change = ((price - prev_close) / prev_close * 100) if prev_close else 0

        # 최근 거래일 데이터
        daily = []
        for i in range(len(timestamps)):
            dt = datetime.datetime.fromtimestamp(timestamps[i])
            daily.append({
                "date": dt.strftime("%Y-%m-%d"),
                "open": quote["open"][i],
                "high": quote["high"][i],
                "low": quote["low"][i],
                "close": quote["close"][i],
                "volume": quote["volume"][i],
            })

        return {
            "symbol": symbol,
            "price": price,
            "prev_close": prev_close,
            "change_pct": round(change, 2),
            "currency": meta.get("currency", ""),
            "exchange": meta.get("exchangeName", ""),
            "daily": daily,
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e), "price": 0, "change_pct": 0}


def collect_all():
    """모든 시장 데이터를 수집하여 구조화된 딕셔너리 반환"""
    now = datetime.datetime.now(KST)
    result = {
        "collected_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "indices": {},
        "commodities": {},
        "kr_stocks": {},
        "us_stocks": {},
    }

    print("📊 지수 데이터 수집 중...")
    for sym, name in INDICES.items():
        data = fetch_chart(sym)
        data["name"] = name
        result["indices"][sym] = data
        arrow = "▲" if data["change_pct"] > 0 else "▼" if data["change_pct"] < 0 else "─"
        print(f"  {name:10s} | {data['price']:>12,.2f} | {arrow}{abs(data['change_pct']):.2f}%")

    print("\n💱 원자재/환율 수집 중...")
    for sym, name in COMMODITIES.items():
        data = fetch_chart(sym)
        data["name"] = name
        result["commodities"][sym] = data
        arrow = "▲" if data["change_pct"] > 0 else "▼" if data["change_pct"] < 0 else "─"
        print(f"  {name:15s} | {data['price']:>12,.2f} | {arrow}{abs(data['change_pct']):.2f}%")

    print("\n🇰🇷 한국 주요 종목 수집 중...")
    for sym, name in KR_STOCKS.items():
        data = fetch_chart(sym)
        data["name"] = name
        result["kr_stocks"][sym] = data
        arrow = "▲" if data["change_pct"] > 0 else "▼" if data["change_pct"] < 0 else "─"
        print(f"  {name:12s} | {data['price']:>12,.0f} KRW | {arrow}{abs(data['change_pct']):.2f}%")

    print("\n🇺🇸 미국 Mag7 수집 중...")
    for sym, name in US_STOCKS.items():
        data = fetch_chart(sym)
        data["name"] = name
        result["us_stocks"][sym] = data
        arrow = "▲" if data["change_pct"] > 0 else "▼" if data["change_pct"] < 0 else "─"
        print(f"  {name:10s} | ${data['price']:>10,.2f} | {arrow}{abs(data['change_pct']):.2f}%")

    return result


def save_json(data, filename=None):
    """수집된 데이터를 JSON 파일로 저장"""
    if filename is None:
        filename = f"market_data_{data['date']}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 데이터 저장 완료: {filename}")
    return filename


if __name__ == "__main__":
    print("=" * 60)
    print("  StockBizView 시장 데이터 수집")
    print(f"  {datetime.datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')}")
    print("=" * 60)
    print()

    data = collect_all()
    save_json(data, os.path.join(os.path.dirname(os.path.abspath(__file__)), "latest_market_data.json"))

    # 요약 출력
    print("\n" + "=" * 60)
    print("  수집 요약")
    print("=" * 60)
    idx = data["indices"]
    kospi = idx.get("^KS11", {})
    kosdaq = idx.get("^KQ11", {})
    sp500 = idx.get("^GSPC", {})
    nasdaq = idx.get("^IXIC", {})
    usdkrw = data["commodities"].get("KRW=X", {})

    print(f"  KOSPI  {kospi.get('price',0):>10,.2f} ({kospi.get('change_pct',0):+.2f}%)")
    print(f"  KOSDAQ {kosdaq.get('price',0):>10,.2f} ({kosdaq.get('change_pct',0):+.2f}%)")
    print(f"  S&P500 {sp500.get('price',0):>10,.2f} ({sp500.get('change_pct',0):+.2f}%)")
    print(f"  NASDAQ {nasdaq.get('price',0):>10,.2f} ({nasdaq.get('change_pct',0):+.2f}%)")
    print(f"  USD/KRW{usdkrw.get('price',0):>10,.2f} ({usdkrw.get('change_pct',0):+.2f}%)")

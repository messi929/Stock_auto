"""
StockBizView - 홈페이지 실시간 업데이트 모듈
수집된 시장 데이터로 홈페이지 티커바 + Market Pulse를 업데이트
"""

import json
import os
import urllib.request
import base64
import datetime
import re

WP_URL = os.environ.get("WP_URL", "https://stockbizview.com")
WP_USER = os.environ.get("WP_USER", "messi929@naver.com")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "s5cW A0gL vzNU AcgS exFC OL0r")


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


def _change_class(pct):
    return "up" if pct > 0 else "down" if pct < 0 else "flat"


def _change_arrow(pct):
    return "▲" if pct > 0 else "▼" if pct < 0 else "─"


def _pulse_color(pct):
    if pct > 0:
        return "#f85149"
    elif pct < 0:
        return "#3fb950"
    return "#8b949e"


def _fmt(n, decimals=0, prefix="", suffix=""):
    if n is None or n == 0:
        return "N/A"
    if decimals == 0:
        return f"{prefix}{n:,.0f}{suffix}"
    return f"{prefix}{n:,.{decimals}f}{suffix}"


def build_ticker_html(data):
    """티커바 HTML 생성"""
    idx = data.get("indices", {})
    comm = data.get("commodities", {})

    items = [
        ("KOSPI", idx.get("^KS11", {})),
        ("KOSDAQ", idx.get("^KQ11", {})),
        ("S&amp;P 500", idx.get("^GSPC", {})),
        ("NASDAQ", idx.get("^IXIC", {})),
        ("USD/KRW", comm.get("KRW=X", {})),
        ("BTC", comm.get("BTC-USD", {})),
    ]

    rows = []
    for name, d in items:
        price = d.get("price", 0)
        pct = d.get("change_pct", 0)
        cls = _change_class(pct)
        arrow = _change_arrow(pct)

        if name == "BTC":
            price_str = f"${price:,.0f}"
        elif name == "USD/KRW":
            price_str = f"{price:,.0f}"
        elif name in ("KOSPI", "KOSDAQ"):
            price_str = f"{price:,.0f}" if price > 100 else f"{price:,.2f}"
        else:
            price_str = f"{price:,.0f}" if price > 1000 else f"{price:,.2f}"

        rows.append(f"""  <div class="sbv-ticker-item" role="group" aria-label="{name} {price_str} {arrow}{abs(pct):.2f}%">
    <div class="sbv-ticker-name">{name}</div>
    <div class="sbv-ticker-price">{price_str}</div>
    <div class="sbv-ticker-change {cls}" aria-hidden="true">{arrow} {abs(pct):.2f}%</div>
  </div>""")

    return '<div class="sbv-ticker-bar" role="region" aria-label="실시간 시장 지표">\n' + "\n".join(rows) + "\n</div>"


def build_pulse_html(data):
    """Market Pulse HTML 생성"""
    comm = data.get("commodities", {})

    vix = comm.get("^VIX", {})
    wti = comm.get("CL=F", {})
    gold = comm.get("GC=F", {})
    tnx = comm.get("^TNX", {})
    dxy = comm.get("DX-Y.NYB", {})
    btc = comm.get("BTC-USD", {})

    # VIX 레벨 텍스트
    vix_val = vix.get("price", 0)
    if vix_val >= 30:
        vix_label = "Extreme Fear"
        vix_color = "#f85149"
    elif vix_val >= 20:
        vix_label = "High Vol"
        vix_color = "#f85149"
    elif vix_val >= 15:
        vix_label = "Normal"
        vix_color = "#d29922"
    else:
        vix_label = "Low Vol"
        vix_color = "#3fb950"

    items = []

    # VIX
    items.append(f"""    <div class="sbv-pulse-item" role="group" aria-label="VIX {vix_val:.2f} {vix_label}">
      <div class="sbv-pulse-label">VIX</div>
      <div class="sbv-pulse-val">{vix_val:.2f}</div>
      <div class="sbv-pulse-chg" style="color:{vix_color};">{vix_label}</div>
    </div>""")

    # WTI
    wti_pct = wti.get("change_pct", 0)
    items.append(f"""    <div class="sbv-pulse-item" role="group" aria-label="WTI 원유 ${wti.get('price', 0):,.2f} {_change_arrow(wti_pct)}{abs(wti_pct):.2f}%">
      <div class="sbv-pulse-label">WTI 원유</div>
      <div class="sbv-pulse-val">${wti.get('price', 0):,.2f}</div>
      <div class="sbv-pulse-chg" style="color:{_pulse_color(wti_pct)};">{_change_arrow(wti_pct)} {abs(wti_pct):.2f}%</div>
    </div>""")

    # Gold
    gold_pct = gold.get("change_pct", 0)
    items.append(f"""    <div class="sbv-pulse-item" role="group" aria-label="금 ${gold.get('price', 0):,.0f} {_change_arrow(gold_pct)}{abs(gold_pct):.2f}%">
      <div class="sbv-pulse-label">금</div>
      <div class="sbv-pulse-val">${gold.get('price', 0):,.0f}</div>
      <div class="sbv-pulse-chg" style="color:{_pulse_color(gold_pct)};">{_change_arrow(gold_pct)} {abs(gold_pct):.2f}%</div>
    </div>""")

    # US 10Y
    tnx_pct = tnx.get("change_pct", 0)
    tnx_val = tnx.get("price", 0)
    items.append(f"""    <div class="sbv-pulse-item" role="group" aria-label="미국 10년 국채 {tnx_val:.2f}% {_change_arrow(tnx_pct)}{abs(tnx_pct):.2f}%">
      <div class="sbv-pulse-label">US 10Y</div>
      <div class="sbv-pulse-val">{tnx_val:.2f}%</div>
      <div class="sbv-pulse-chg" style="color:{_pulse_color(tnx_pct)};">{_change_arrow(tnx_pct)} {abs(tnx_pct):.2f}%</div>
    </div>""")

    # Dollar Index
    dxy_pct = dxy.get("change_pct", 0)
    items.append(f"""    <div class="sbv-pulse-item" role="group" aria-label="달러인덱스 {dxy.get('price', 0):,.2f} {_change_arrow(dxy_pct)}{abs(dxy_pct):.2f}%">
      <div class="sbv-pulse-label">달러인덱스</div>
      <div class="sbv-pulse-val">{dxy.get('price', 0):,.2f}</div>
      <div class="sbv-pulse-chg" style="color:{_pulse_color(dxy_pct)};">{_change_arrow(dxy_pct)} {abs(dxy_pct):.2f}%</div>
    </div>""")

    # BTC
    btc_pct = btc.get("change_pct", 0)
    items.append(f"""    <div class="sbv-pulse-item" role="group" aria-label="비트코인 ${btc.get('price', 0):,.0f} {_change_arrow(btc_pct)}{abs(btc_pct):.2f}%">
      <div class="sbv-pulse-label">비트코인</div>
      <div class="sbv-pulse-val">${btc.get('price', 0):,.0f}</div>
      <div class="sbv-pulse-chg" style="color:{_pulse_color(btc_pct)};">{_change_arrow(btc_pct)} {abs(btc_pct):.2f}%</div>
    </div>""")

    return f"""<div class="sbv-pulse" role="region" aria-label="Market Pulse - 주요 자산 현황">
  <div class="sbv-pulse-title">
    <span class="sbv-pulse-dot" aria-hidden="true"></span>
    Market Pulse
  </div>
  <div class="sbv-pulse-grid">
{chr(10).join(items)}
  </div>
</div>"""


def update_homepage(data):
    """홈페이지 템플릿의 티커바 + Market Pulse를 최신 데이터로 업데이트"""
    print("\n🏠 홈페이지 업데이트 중...")

    # 현재 홈 템플릿 가져오기
    templates = _wp_request("templates?per_page=50")
    home = None
    for t in templates:
        if t["slug"] == "home":
            home = t
            break

    if not home:
        print("  ❌ home 템플릿을 찾을 수 없습니다")
        return False

    content = home["content"]["raw"]

    # 새 티커바 + Market Pulse HTML
    new_ticker = build_ticker_html(data)
    new_pulse = build_pulse_html(data)

    # 타임스탬프 업데이트
    KST = datetime.timezone(datetime.timedelta(hours=9))
    now_kst = datetime.datetime.now(KST)
    new_timestamp = now_kst.strftime("%Y.%m.%d %H:%M KST")
    new_content = re.sub(
        r'데이터 업데이트: [\d.]+\s+[\d:]+\s+KST',
        f'데이터 업데이트: {new_timestamp}',
        content,
        count=1,
    )

    # 티커바 블록 교체
    ticker_pattern = r'(<!-- wp:html -->\n)<div class="sbv-ticker-bar">.*?</div>\n(<!-- /wp:html -->)'
    ticker_replacement = f'\\1{new_ticker}\n\\2'
    new_content = re.sub(ticker_pattern, ticker_replacement, new_content, count=1, flags=re.DOTALL)

    # Market Pulse 블록 교체 (기존 위치에서)
    pulse_pattern = r'<!-- wp:html -->\n<div class="sbv-pulse">.*?</div>\n<!-- /wp:html -->'
    new_pulse_block = f'<!-- wp:html -->\n{new_pulse}\n<!-- /wp:html -->'

    if re.search(pulse_pattern, new_content, flags=re.DOTALL):
        # 기존 pulse 제거
        new_content = re.sub(pulse_pattern, '', new_content, count=1, flags=re.DOTALL)

    # 티커바 바로 다음에 Market Pulse 삽입
    ticker_end = '<!-- /wp:html -->\n\n<!-- wp:html -->\n<div class="sbv-section-header">'
    pulse_insert = f'<!-- /wp:html -->\n\n{new_pulse_block}\n\n<!-- wp:html -->\n<div class="sbv-section-header">'
    new_content = new_content.replace(ticker_end, pulse_insert, 1)

    # 중복 빈 줄 정리
    while '\n\n\n\n' in new_content:
        new_content = new_content.replace('\n\n\n\n', '\n\n\n')

    # 업데이트
    template_id = home["id"]
    _wp_request(f"templates/{template_id}", method="POST", data={"content": new_content})

    print(f"  ✅ 홈페이지 업데이트 완료 (티커바 + Market Pulse)")
    return True


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from generate_report import load_data

    data = load_data()
    update_homepage(data)

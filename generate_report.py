"""
StockBizView - 리포트 생성 모듈
데이터 + AI 분석 텍스트를 결합하여 애널리스트급 HTML 리포트 생성
"""

import json
import os
import datetime
import sys
import io


def load_data(filepath=None):
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "latest_market_data.json")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def fmt_num(n, decimals=0):
    if n is None or n == 0:
        return "N/A"
    if decimals == 0:
        return f"{n:,.0f}"
    return f"{n:,.{decimals}f}"


def change_color(pct):
    if pct > 0:
        return "#ef4444"
    elif pct < 0:
        return "#3b82f6"
    return "#9ca3af"


def change_arrow(pct):
    if pct > 0:
        return "▲"
    elif pct < 0:
        return "▼"
    return "─"


def metric_card(label, value, change_pct, prefix="", suffix=""):
    color = change_color(change_pct)
    arrow = change_arrow(change_pct)
    cls = "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"
    return f"""<div class="sbv-metric" role="group" aria-label="{label} {prefix}{value}{suffix} {arrow}{abs(change_pct):.2f}%">
  <div class="sbv-metric-label">{label}</div>
  <div class="sbv-metric-value">{prefix}{value}{suffix}</div>
  <div class="sbv-metric-change {cls}" style="color:{color}">{arrow} {abs(change_pct):.2f}%</div>
</div>"""


def bar_chart_row(name, value, change_pct, max_abs_pct=10):
    color = change_color(change_pct)
    arrow = change_arrow(change_pct)
    cls = "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"
    width = min(abs(change_pct) / max_abs_pct * 100, 100)
    return f"""<div class="sbv-bar-row" role="group" aria-label="{name} {arrow}{abs(change_pct):.2f}%">
  <span class="sbv-bar-name">{name}</span>
  <div class="sbv-bar-track" aria-hidden="true">
    <div class="sbv-bar-fill {cls}" style="width:{width:.0f}%;background:{color}"></div>
  </div>
  <span class="sbv-bar-pct {cls}" style="color:{color}">{arrow}{abs(change_pct):.2f}%</span>
</div>"""


def analysis_section(title_text, paragraphs):
    """AI 분석 내러티브 섹션 생성"""
    html = f'<div class="sbv-section"><div class="sbv-section-title">{title_text}</div>'
    for p in paragraphs:
        html += f'<p class="sbv-paragraph">{p}</p>'
    html += '</div>'
    return html


CSS = """<style>
.sbv-wrap *{box-sizing:border-box}
.sbv-wrap{max-width:800px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
.sbv-header{background:linear-gradient(135deg,#0d1117,#161b22);border-left:4px solid #3fb950;padding:24px 28px;margin-bottom:28px;border-radius:6px}
.sbv-date{font-size:11px;font-weight:700;letter-spacing:2px;color:#3fb950;text-transform:uppercase;margin-bottom:6px}
.sbv-title{font-size:22px;font-weight:800;color:#f0f6fc;margin:0 0 4px 0}
.sbv-subtitle{font-size:13px;color:#8b949e;letter-spacing:1px}
.sbv-section{background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:24px;margin-bottom:24px}
.sbv-section-title{font-size:16px;font-weight:700;color:#f0f6fc;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #30363d}
.sbv-paragraph{color:#c9d1d9;line-height:1.8;margin:10px 0;font-size:14px}
.sbv-metric{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:18px 16px;flex:1 1 130px;text-align:center}
.sbv-metric-label{font-size:11px;font-weight:700;letter-spacing:1.5px;color:#8b949e;text-transform:uppercase;margin-bottom:8px}
.sbv-metric-value{font-size:18px;font-weight:800;color:#f0f6fc;margin-bottom:4px}
.sbv-metric-change{font-size:13px;font-weight:600}
.sbv-metrics{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:28px}
.sbv-bar-row{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.sbv-bar-name{width:100px;min-width:100px;font-size:13px;font-weight:600;color:#c9d1d9;text-align:right}
.sbv-bar-track{flex:1;height:20px;background:#21262d;border-radius:4px;overflow:hidden}
.sbv-bar-fill{height:100%;border-radius:4px}
.sbv-bar-pct{width:80px;min-width:80px;font-size:13px;font-weight:700}
.sbv-table{width:100%;border-collapse:collapse;font-size:13px}
.sbv-table th{background:#161b22;color:#8b949e;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:10px 14px;text-align:left;border-bottom:1px solid #30363d}
.sbv-table td{padding:10px 14px;border-bottom:1px solid #21262d;color:#c9d1d9}
.sbv-table tr:hover{background:#161b22}
.sbv-strategy{background:linear-gradient(135deg,#0d1117,#1a1f2e);border:1px solid #1f6feb;border-radius:8px;padding:24px;margin-bottom:24px}
.sbv-strategy-title{color:#58a6ff;font-size:16px;font-weight:700;margin-bottom:12px}
.sbv-strategy p{color:#c9d1d9;line-height:1.7;margin:8px 0}
.sbv-disclaimer{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:16px;margin-top:24px;font-size:11px;color:#8b949e;text-align:center}
.sbv-executive{background:linear-gradient(135deg,#0d1117,#101820);border:1px solid #3fb950;border-radius:8px;padding:24px;margin-bottom:24px}
.sbv-executive-title{color:#3fb950;font-size:14px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px}
.sbv-executive-item{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px}
.sbv-executive-num{background:#3fb950;color:#0d1117;font-size:12px;font-weight:800;width:22px;height:22px;min-width:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-top:2px}
.sbv-executive-text{color:#e6edf3;font-size:14px;line-height:1.6;font-weight:500}
.sbv-keynumber{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px 20px;margin-bottom:10px;display:flex;align-items:flex-start;gap:12px}
.sbv-keynumber-icon{font-size:20px;min-width:28px;text-align:center}
.sbv-keynumber-text{color:#c9d1d9;font-size:13px;line-height:1.6}
.sbv-tech{background:#0d1117;border:1px solid #8957e5;border-radius:8px;padding:24px;margin-bottom:24px}
.sbv-tech-title{color:#d2a8ff;font-size:16px;font-weight:700;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #30363d}
.sbv-money{background:#0d1117;border:1px solid #f0883e;border-radius:8px;padding:24px;margin-bottom:24px}
.sbv-money-title{color:#f0883e;font-size:16px;font-weight:700;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #30363d}
.sbv-outlook{background:linear-gradient(135deg,#0d1117,#0d1520);border:1px solid #58a6ff;border-radius:8px;padding:24px;margin-bottom:24px}
.sbv-outlook-title{color:#58a6ff;font-size:16px;font-weight:700;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #30363d}
</style>"""


def _build_weekly_daily_breakdown(data_dict):
    """daily 배열에서 요일별 등락률 추출"""
    lines = []
    for sym, d in data_dict.items():
        daily = d.get("daily", [])
        if len(daily) < 2:
            continue
        name = d.get("name", sym)
        day_changes = []
        for i in range(1, len(daily)):
            prev_close = daily[i-1].get("close") or 0
            curr_close = daily[i].get("close") or 0
            if prev_close:
                chg = (curr_close - prev_close) / prev_close * 100
                day_changes.append(f"{daily[i]['date']}: {chg:+.2f}%")
        # 주간 종합 (첫째 날 시가 → 마지막 날 종가)
        week_open = daily[0].get("open") or daily[0].get("close") or 0
        week_close = daily[-1].get("close") or 0
        week_chg = ((week_close - week_open) / week_open * 100) if week_open else 0
        # 주간 고/저
        highs = [x.get("high") or 0 for x in daily]
        lows = [x.get("low") or 0 for x in daily if x.get("low")]
        week_high = max(highs) if highs else 0
        week_low = min(lows) if lows else 0
        lines.append(f"{name}: 현재가 {d.get('price',0):,.2f} | 주간 {week_chg:+.2f}% | 고 {week_high:,.2f} 저 {week_low:,.2f}")
        lines.append(f"  요일별: {', '.join(day_changes)}")
    return "\n".join(lines)


def build_data_summary(data, report_type="post_market"):
    """AI 분석 프롬프트용 데이터 요약 텍스트 생성"""
    idx = data["indices"]
    comm = data["commodities"]
    kr = data["kr_stocks"]
    us = data["us_stocks"]

    is_weekly = report_type in ("weekly_recap_kr", "weekly_recap_us")

    lines = []

    if is_weekly:
        lines.append("=== 주간 데이터 (요일별 흐름 포함) ===\n")
        lines.append("--- 주요 지수 ---")
        lines.append(_build_weekly_daily_breakdown(idx))
        lines.append("\n--- 원자재/환율 ---")
        lines.append(_build_weekly_daily_breakdown(comm))
        lines.append("\n--- 한국 주요종목 ---")
        lines.append(_build_weekly_daily_breakdown(kr))
        lines.append("\n--- 미국 Mag7 ---")
        lines.append(_build_weekly_daily_breakdown(us))
    else:
        lines.append("=== 주요 지수 ===")
        for sym, d in idx.items():
            lines.append(f"{d.get('name','')}: {d.get('price',0):,.2f} ({d.get('change_pct',0):+.2f}%)")

        lines.append("\n=== 원자재/환율 ===")
        for sym, d in comm.items():
            lines.append(f"{d.get('name','')}: {d.get('price',0):,.2f} ({d.get('change_pct',0):+.2f}%)")

        lines.append("\n=== 한국 주요종목 ===")
        for sym, d in sorted(kr.items(), key=lambda x: x[1].get('change_pct', 0), reverse=True):
            lines.append(f"{d.get('name','')}: {d.get('price',0):,.0f}원 ({d.get('change_pct',0):+.2f}%)")

        # 장후 리포트는 미장 미개장이므로 Mag7 제외
        if report_type != "post_market":
            lines.append("\n=== 미국 Mag7 ===")
            for sym, d in sorted(us.items(), key=lambda x: x[1].get('change_pct', 0), reverse=True):
                lines.append(f"{d.get('name','')}: ${d.get('price',0):,.2f} ({d.get('change_pct',0):+.2f}%)")

    return "\n".join(lines)


def _calc_weekly_change(item):
    """daily 배열에서 주간 등락률 계산 (시가 → 종가)"""
    daily = item.get("daily", [])
    if len(daily) < 2:
        return item.get("change_pct", 0)
    week_open = daily[0].get("open") or daily[0].get("close") or 0
    week_close = daily[-1].get("close") or 0
    if week_open:
        return round((week_close - week_open) / week_open * 100, 2)
    return item.get("change_pct", 0)


def _weekly_daily_bars(item):
    """daily 배열에서 요일별 등락률 bar 차트 데이터 생성"""
    daily = item.get("daily", [])
    bars = []
    for i in range(1, len(daily)):
        prev_close = daily[i-1].get("close") or 0
        curr_close = daily[i].get("close") or 0
        if prev_close:
            chg = round((curr_close - prev_close) / prev_close * 100, 2)
        else:
            chg = 0
        # 날짜에서 요일 추출
        date_str = daily[i].get("date", "")
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            day_names = ["월", "화", "수", "목", "금", "토", "일"]
            day_label = day_names[dt.weekday()]
        except (ValueError, IndexError):
            day_label = date_str[-5:]  # MM-DD
        bars.append((day_label, chg))
    return bars


def _build_toc(analysis, report_type):
    """리포트 목차(Table of Contents) HTML 생성"""
    is_weekly = report_type in ("weekly_kr", "weekly_us")
    sections = []
    if analysis.get("executive_summary"):
        sections.append(("sec-summary", "📌 핵심 요약"))
    if analysis.get("market_overview"):
        sections.append(("sec-overview", "📰 시황 분석" if not is_weekly else "📰 주간 시황 분석"))
    sections.append(("sec-data", "📊 시장 데이터"))
    if analysis.get("sector_analysis"):
        sections.append(("sec-sector", "🔍 섹터 · 종목 분석"))
    if analysis.get("technical_levels"):
        sections.append(("sec-tech", "📊 기술적 분석"))
    if analysis.get("money_flow"):
        sections.append(("sec-money", "💰 자금 흐름 · 수급 분석"))
    sections.append(("sec-commodity", "💱 원자재 · 환율 · 금리"))
    if analysis.get("key_numbers"):
        sections.append(("sec-numbers", "🔢 핵심 숫자"))
    if analysis.get("risk_factors"):
        sections.append(("sec-risk", "⚠️ 리스크 요인"))
    if analysis.get("strategy"):
        sections.append(("sec-strategy", "📋 투자 전략"))
    if analysis.get("tomorrow_outlook"):
        sections.append(("sec-outlook", "🔮 전망"))

    if len(sections) < 3:
        return ""

    html = '<nav class="sbv-toc" aria-label="목차"><div class="sbv-toc-title">📑 목차</div><ul class="sbv-toc-list">'
    for anchor, label in sections:
        html += f'<li><a href="#{anchor}" style="color:#58a6ff;text-decoration:none;font-size:13px">{label}</a></li>'
    html += '</ul></nav>'
    return html


def _build_internal_links(report_type):
    """관련 리포트 카테고리 내부링크 HTML 생성"""
    WP_URL = os.environ.get("WP_URL", "https://stockbizview.com")
    links = {
        "pre": [
            ("장후 리포트", f"{WP_URL}/category/post-market/"),
            ("미국 시장 분석", f"{WP_URL}/category/us-market/"),
            ("투자 전략", f"{WP_URL}/category/investment-strategy/"),
        ],
        "post": [
            ("장전 리포트", f"{WP_URL}/category/pre-market/"),
            ("종목 분석", f"{WP_URL}/category/stock-analysis/"),
            ("한국 시장 심층", f"{WP_URL}/category/korea-market/"),
        ],
        "weekly_kr": [
            ("미국 시장 주간 리뷰", f"{WP_URL}/category/us-market/"),
            ("장전 리포트", f"{WP_URL}/category/pre-market/"),
            ("종목 분석", f"{WP_URL}/category/stock-analysis/"),
            ("투자 전략", f"{WP_URL}/category/investment-strategy/"),
        ],
        "weekly_us": [
            ("한국 시장 주간 리뷰", f"{WP_URL}/category/korea-market/"),
            ("장후 리포트", f"{WP_URL}/category/post-market/"),
            ("종목 분석", f"{WP_URL}/category/stock-analysis/"),
            ("투자 전략", f"{WP_URL}/category/investment-strategy/"),
        ],
    }

    items = links.get(report_type, [
        ("장전 리포트", f"{WP_URL}/category/pre-market/"),
        ("장후 리포트", f"{WP_URL}/category/post-market/"),
        ("투자 전략", f"{WP_URL}/category/investment-strategy/"),
    ])

    html = '<div class="sbv-related" style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin-top:24px;margin-bottom:24px">'
    html += '<div style="color:#8b949e;font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px">📂 관련 리포트</div>'
    html += '<div style="display:flex;flex-wrap:wrap;gap:8px">'
    for label, url in items:
        html += f'<a href="{url}" style="display:inline-block;background:#21262d;color:#58a6ff;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:600;text-decoration:none;border:1px solid #30363d">{label}</a>'
    html += '</div></div>'
    return html


def generate_report(data, report_type="post", analysis=None):
    """
    통합 리포트 생성
    - data: 시장 데이터
    - report_type: "pre" (장전), "post" (장후), "weekly_kr" (한국 주간), "weekly_us" (미국 주간)
    - analysis: AI가 생성한 분석 dict
    """
    date_str = data["date"]
    today = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    date_display = today.strftime("%Y.%m.%d")

    idx = data["indices"]
    comm = data["commodities"]
    kr = data["kr_stocks"]
    us = data["us_stocks"]

    sp500 = idx.get("^GSPC", {})
    nasdaq = idx.get("^IXIC", {})
    dow = idx.get("^DJI", {})
    kospi = idx.get("^KS11", {})
    kosdaq = idx.get("^KQ11", {})
    usdkrw = comm.get("KRW=X", {})
    wti = comm.get("CL=F", {})
    gold = comm.get("GC=F", {})
    btc = comm.get("BTC-USD", {})
    vix = comm.get("^VIX", {})
    tnx = comm.get("^TNX", {})

    kr_sorted = sorted(kr.values(), key=lambda x: x.get("change_pct", 0), reverse=True)
    us_sorted = sorted(us.values(), key=lambda x: x.get("change_pct", 0), reverse=True)

    # 분석이 없으면 기본값
    if analysis is None:
        analysis = {}
    headline = analysis.get("headline", "")

    is_pre = report_type == "pre"
    is_weekly = report_type in ("weekly_kr", "weekly_us")
    is_weekly_kr = report_type == "weekly_kr"
    is_weekly_us = report_type == "weekly_us"

    if is_weekly_kr:
        label = "주간 한국"
    elif is_weekly_us:
        label = "주간 미국"
    elif is_pre:
        label = "장전"
    else:
        label = "장후"

    # === TOC용 추가 CSS ===
    toc_css = """
.sbv-toc{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px 20px;margin-bottom:24px}
.sbv-toc-title{color:#8b949e;font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px}
.sbv-toc-list{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:6px 16px}
.sbv-toc-list li{margin:0}
.sbv-weekly-flow{display:flex;gap:4px;align-items:flex-end;height:40px;margin:8px 0}
.sbv-weekly-bar{flex:1;border-radius:2px 2px 0 0;min-width:20px;position:relative}
.sbv-weekly-bar-label{position:absolute;bottom:-18px;left:50%;transform:translateX(-50%);font-size:10px;color:#8b949e;white-space:nowrap}
"""

    # === HTML 조립 ===
    html = CSS.replace("</style>", toc_css + "</style>")
    html += '<div class="sbv-wrap">'

    # 헤더
    if is_weekly:
        # 주간 리포트: 주간 날짜 범위 표시
        daily_data = kospi.get("daily", []) if is_weekly_kr else sp500.get("daily", [])
        if daily_data:
            week_start = daily_data[0].get("date", date_str)
            week_end = daily_data[-1].get("date", date_str)
            try:
                ws = datetime.datetime.strptime(week_start, "%Y-%m-%d").strftime("%m.%d")
                we = datetime.datetime.strptime(week_end, "%Y-%m-%d").strftime("%m.%d")
                date_range = f"{ws}~{we}"
            except ValueError:
                date_range = date_display
        else:
            date_range = date_display

        if headline:
            subtitle = headline
        elif is_weekly_kr:
            wk_chg = _calc_weekly_change(kospi)
            subtitle = f"KOSPI 주간 {change_arrow(wk_chg)}{abs(wk_chg):.2f}% · KOSDAQ 주간 {change_arrow(_calc_weekly_change(kosdaq))}{abs(_calc_weekly_change(kosdaq)):.2f}%"
        else:
            wk_chg = _calc_weekly_change(sp500)
            subtitle = f"S&P 500 주간 {change_arrow(wk_chg)}{abs(wk_chg):.2f}% · NASDAQ 주간 {change_arrow(_calc_weekly_change(nasdaq))}{abs(_calc_weekly_change(nasdaq)):.2f}%"

        html += f"""
<div class="sbv-header" style="border-left:4px solid #58a6ff">
  <div class="sbv-date">STOCKBIZVIEW {label.upper()} REVIEW · {date_range}</div>
  <h1 class="sbv-title">{subtitle}</h1>
</div>
"""
    else:
        if headline:
            subtitle = headline
        else:
            kospi_chg = kospi.get("change_pct", 0)
            subtitle = f"KOSPI {change_arrow(kospi_chg)}{abs(kospi_chg):.2f}% · KOSDAQ {change_arrow(kosdaq.get('change_pct',0))}{abs(kosdaq.get('change_pct',0)):.2f}% · USD/KRW {fmt_num(usdkrw.get('price',0),0)}원"

        html += f"""
<div class="sbv-header">
  <div class="sbv-date">STOCKBIZVIEW {label.upper()} · {date_display}</div>
  <h1 class="sbv-title">{subtitle}</h1>
</div>
"""

    # 목차 (TOC)
    html += _build_toc(analysis, report_type)

    # 메트릭 카드 — 주간 리포트는 주간 등락률 사용
    html += '<div class="sbv-metrics" role="region" aria-label="주요 시장 지표">'
    if is_weekly_us:
        html += metric_card("S&P 500", fmt_num(sp500.get("price", 0), 2), _calc_weekly_change(sp500))
        html += metric_card("NASDAQ", fmt_num(nasdaq.get("price", 0), 2), _calc_weekly_change(nasdaq))
        html += metric_card("다우존스", fmt_num(dow.get("price", 0), 2), _calc_weekly_change(dow))
    elif is_weekly_kr:
        html += metric_card("KOSPI", fmt_num(kospi.get("price", 0), 2), _calc_weekly_change(kospi))
        html += metric_card("KOSDAQ", fmt_num(kosdaq.get("price", 0), 2), _calc_weekly_change(kosdaq))
    elif is_pre:
        html += metric_card("S&P 500", fmt_num(sp500.get("price", 0), 2), sp500.get("change_pct", 0))
        html += metric_card("NASDAQ", fmt_num(nasdaq.get("price", 0), 2), nasdaq.get("change_pct", 0))
        html += metric_card("KOSPI", fmt_num(kospi.get("price", 0), 2), kospi.get("change_pct", 0))
    else:
        html += metric_card("KOSPI", fmt_num(kospi.get("price", 0), 2), kospi.get("change_pct", 0))
        html += metric_card("KOSDAQ", fmt_num(kosdaq.get("price", 0), 2), kosdaq.get("change_pct", 0))
    chg_fn = _calc_weekly_change if is_weekly else lambda x: x.get("change_pct", 0)
    html += metric_card("USD/KRW", fmt_num(usdkrw.get("price", 0), 0), chg_fn(usdkrw), suffix="원")
    html += metric_card("WTI", fmt_num(wti.get("price", 0), 2), chg_fn(wti), prefix="$")
    html += metric_card("VIX", fmt_num(vix.get("price", 0), 1), chg_fn(vix))
    html += metric_card("BTC", fmt_num(btc.get("price", 0), 0), chg_fn(btc), prefix="$")
    html += '</div>'

    # 📌 Executive Summary (핵심 요약)
    if analysis.get("executive_summary"):
        html += f'<div class="sbv-executive" id="sec-summary"><div class="sbv-executive-title">📌 핵심 요약</div>'
        for i, point in enumerate(analysis["executive_summary"], 1):
            html += f'<div class="sbv-executive-item"><div class="sbv-executive-num">{i}</div><div class="sbv-executive-text">{point}</div></div>'
        html += '</div>'

    # 📰 시황 분석 (AI 내러티브)
    if analysis.get("market_overview"):
        overview_title = "📰 주간 시황 분석" if is_weekly else "📰 시황 분석"
        html += f'<div class="sbv-section" id="sec-overview"><div class="sbv-section-title">{overview_title}</div>'
        for p in analysis["market_overview"]:
            html += f'<p class="sbv-paragraph">{p}</p>'
        html += '</div>'

    # === 주간 리포트 전용: 요일별 흐름 미니 차트 ===
    if is_weekly:
        html += '<div class="sbv-section" id="sec-data"><div class="sbv-section-title">📅 요일별 흐름</div>'
        # 주요 지수 요일별 bar
        focus_items = []
        if is_weekly_kr:
            focus_items = [("KOSPI", kospi), ("KOSDAQ", kosdaq), ("USD/KRW", usdkrw)]
        else:
            focus_items = [("S&P 500", sp500), ("NASDAQ", nasdaq), ("다우존스", dow)]

        for name, item in focus_items:
            daily_bars = _weekly_daily_bars(item)
            if not daily_bars:
                continue
            wk_chg = _calc_weekly_change(item)
            html += f'<div style="margin-bottom:16px"><div style="font-size:13px;font-weight:700;color:#f0f6fc;margin-bottom:6px">{name} <span style="color:{change_color(wk_chg)};font-size:12px">(주간 {change_arrow(wk_chg)}{abs(wk_chg):.2f}%)</span></div>'
            html += '<div class="sbv-weekly-flow">'
            max_abs = max(abs(c) for _, c in daily_bars) if daily_bars else 1
            for day_label, chg in daily_bars:
                h = max(int(abs(chg) / max_abs * 36), 4) if max_abs else 4
                color = change_color(chg)
                html += f'<div class="sbv-weekly-bar" style="height:{h}px;background:{color}"><div class="sbv-weekly-bar-label">{day_label}</div></div>'
            html += '</div></div>'
        html += '</div>'

    # 지수 바 차트
    if is_pre or is_weekly_us:
        html += '<div class="sbv-section"><div class="sbv-section-title">🇺🇸 미국 시장 지수</div>'
        if is_weekly_us:
            html += bar_chart_row("S&P 500", sp500.get("price", 0), _calc_weekly_change(sp500))
            html += bar_chart_row("NASDAQ", nasdaq.get("price", 0), _calc_weekly_change(nasdaq))
            html += bar_chart_row("다우존스", dow.get("price", 0), _calc_weekly_change(dow))
        else:
            html += bar_chart_row("S&P 500", sp500.get("price", 0), sp500.get("change_pct", 0))
            html += bar_chart_row("NASDAQ", nasdaq.get("price", 0), nasdaq.get("change_pct", 0))
            html += bar_chart_row("다우존스", dow.get("price", 0), dow.get("change_pct", 0))
        html += '</div>'

    # Mag7
    if is_pre or is_weekly_us:
        html += '<div class="sbv-section"><div class="sbv-section-title">🏢 Magnificent 7</div>'
        if is_weekly_us:
            us_weekly = sorted(us.values(), key=lambda x: _calc_weekly_change(x), reverse=True)
            for s in us_weekly:
                html += bar_chart_row(s.get("name", ""), s.get("price", 0), _calc_weekly_change(s))
        else:
            for s in us_sorted:
                html += bar_chart_row(s.get("name", ""), s.get("price", 0), s.get("change_pct", 0))
        html += '</div>'

    # 🔍 섹터 분석 (AI 내러티브)
    if analysis.get("sector_analysis"):
        html += f'<div class="sbv-section" id="sec-sector"><div class="sbv-section-title">🔍 섹터 · 종목 분석</div>'
        for p in analysis["sector_analysis"]:
            html += f'<p class="sbv-paragraph">{p}</p>'
        html += '</div>'

    # 한국 대표주
    if not is_weekly_us:
        if not is_weekly:
            html += '<div class="sbv-section"><div class="sbv-section-title">🇰🇷 한국 대표주</div>'
            for s in kr_sorted:
                html += bar_chart_row(s.get("name", ""), s.get("price", 0), s.get("change_pct", 0))
            html += '</div>'
        else:
            # 주간 한국: 주간 등락률 기준
            kr_weekly = sorted(kr.values(), key=lambda x: _calc_weekly_change(x), reverse=True)
            html += '<div class="sbv-section"><div class="sbv-section-title">🇰🇷 한국 대표주 주간 등락</div>'
            for s in kr_weekly:
                html += bar_chart_row(s.get("name", ""), s.get("price", 0), _calc_weekly_change(s))
            html += '</div>'

    # 📊 기술적 분석 (AI 내러티브)
    if analysis.get("technical_levels"):
        html += f'<div class="sbv-tech" id="sec-tech"><div class="sbv-tech-title">📊 기술적 분석</div>'
        for p in analysis["technical_levels"]:
            html += f'<p class="sbv-paragraph">{p}</p>'
        html += '</div>'

    # 💰 자금 흐름 (AI 내러티브)
    if analysis.get("money_flow"):
        html += f'<div class="sbv-money" id="sec-money"><div class="sbv-money-title">💰 자금 흐름 · 수급 분석</div>'
        for p in analysis["money_flow"]:
            html += f'<p class="sbv-paragraph">{p}</p>'
        html += '</div>'

    # 원자재/환율 테이블
    html += f'<div class="sbv-section" id="sec-commodity"><div class="sbv-section-title">💱 원자재 · 환율 · 금리</div>'
    if is_weekly:
        html += '<table class="sbv-table"><thead><tr><th>항목</th><th>가격</th><th>주간 등락</th></tr></thead><tbody>'
    else:
        html += '<table class="sbv-table"><thead><tr><th>항목</th><th>가격</th><th>등락</th></tr></thead><tbody>'
    for sym, name in [("KRW=X", "USD/KRW"), ("CL=F", "WTI 원유"), ("GC=F", "금"), ("BTC-USD", "비트코인"), ("^VIX", "VIX"), ("^TNX", "10Y 금리")]:
        c = comm.get(sym, {})
        pct = _calc_weekly_change(c) if is_weekly else c.get("change_pct", 0)
        color = change_color(pct)
        arrow = change_arrow(pct)
        prefix = "$" if sym not in ("KRW=X", "^VIX", "^TNX") else ""
        suffix = "원" if sym == "KRW=X" else "%" if sym == "^TNX" else ""
        html += f'<tr><td>{name}</td><td>{prefix}{fmt_num(c.get("price", 0), 2)}{suffix}</td><td style="color:{color}">{arrow} {abs(pct):.2f}%</td></tr>'
    html += '</tbody></table></div>'

    # 🔢 핵심 숫자 (AI)
    if analysis.get("key_numbers"):
        icons = ["📈", "💹", "🔑", "⚡", "🎯"]
        num_title = "🔢 이번 주 핵심 숫자" if is_weekly else "🔢 오늘의 핵심 숫자"
        html += f'<div class="sbv-section" id="sec-numbers"><div class="sbv-section-title">{num_title}</div>'
        for i, num in enumerate(analysis["key_numbers"]):
            icon = icons[i % len(icons)]
            html += f'<div class="sbv-keynumber"><div class="sbv-keynumber-icon">{icon}</div><div class="sbv-keynumber-text">{num}</div></div>'
        html += '</div>'

    # ⚠️ 리스크 요인 (AI 내러티브)
    if analysis.get("risk_factors"):
        html += f'<div class="sbv-section" id="sec-risk"><div class="sbv-section-title">⚠️ 리스크 요인</div>'
        for p in analysis["risk_factors"]:
            html += f'<p class="sbv-paragraph">{p}</p>'
        html += '</div>'

    # 📋 투자 전략 (AI 내러티브)
    if analysis.get("strategy"):
        strategy_title = "📋 다음 주 투자 전략" if is_weekly else "📋 투자 전략"
        html += f'<div class="sbv-strategy" id="sec-strategy"><div class="sbv-strategy-title">{strategy_title}</div>'
        for p in analysis["strategy"]:
            html += f'<p>{p}</p>'
        html += '</div>'

    # 🔮 전망 (AI 내러티브 - 강조 스타일)
    if analysis.get("tomorrow_outlook"):
        if is_weekly:
            outlook_title = "다음 주 전망"
        elif is_pre:
            outlook_title = "오늘 장 전망"
        else:
            outlook_title = "내일 장 전망"
        html += f'<div class="sbv-outlook" id="sec-outlook"><div class="sbv-outlook-title">🔮 {outlook_title}</div>'
        for p in analysis["tomorrow_outlook"]:
            html += f'<p class="sbv-paragraph">{p}</p>'
        html += '</div>'

    # 📂 관련 리포트 내부링크
    html += _build_internal_links(report_type)

    html += '<div class="sbv-disclaimer">⚠️ 본 리포트는 투자 참고 자료이며, 투자 판단의 최종 책임은 투자자 본인에게 있습니다. | StockBizView</div>'

    # SEO: Yoast가 wordCount를 정확히 계산할 수 있도록 plain text 블록 추가
    seo_sections = ["executive_summary", "market_overview", "sector_analysis",
                    "technical_levels", "money_flow", "key_numbers",
                    "risk_factors", "strategy", "tomorrow_outlook"]
    plain_parts = []
    for key in seo_sections:
        items = analysis.get(key, [])
        if isinstance(items, list):
            plain_parts.extend(items)
    if plain_parts:
        plain_text = " ".join(plain_parts)
        html += f'<div class="sbv-seo-text" style="position:absolute;left:-9999px;height:1px;overflow:hidden" aria-hidden="true">{plain_text}</div>'

    html += '</div>'  # close sbv-wrap

    # 제목 생성
    if analysis.get("title"):
        if is_weekly:
            # 주간 리포트: 주간 날짜 범위 사용
            daily_data = kospi.get("daily", []) if is_weekly_kr else sp500.get("daily", [])
            if daily_data:
                try:
                    ws = datetime.datetime.strptime(daily_data[0]["date"], "%Y-%m-%d").strftime("%m.%d")
                    we = datetime.datetime.strptime(daily_data[-1]["date"], "%Y-%m-%d").strftime("%m.%d")
                    title = f"{analysis['title']} — {ws}~{we}"
                except (ValueError, KeyError):
                    title = f"{analysis['title']} — {date_display}"
            else:
                title = f"{analysis['title']} — {date_display}"
        else:
            title = f"{analysis['title']} — {date_display}"
    else:
        kospi_chg = kospi.get("change_pct", 0)
        title = f"KOSPI {kospi_chg:+.1f}% — {date_display}"

    return title, html


if __name__ == "__main__":
    report_type = sys.argv[1] if len(sys.argv) > 1 else "post"
    data = load_data()
    title, html = generate_report(data, report_type)
    print(f"Title: {title}")
    print(f"HTML: {len(html):,} chars")

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


def build_data_summary(data, report_type="post_market"):
    """AI 분석 프롬프트용 데이터 요약 텍스트 생성"""
    idx = data["indices"]
    comm = data["commodities"]
    kr = data["kr_stocks"]
    us = data["us_stocks"]

    lines = []
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


def generate_report(data, report_type="post", analysis=None):
    """
    통합 리포트 생성
    - data: 시장 데이터
    - report_type: "pre" (장전) or "post" (장후)
    - analysis: AI가 생성한 분석 dict:
        {
            "headline": "한줄 헤드라인",
            "market_overview": ["시황 개요 단락1", "단락2", ...],
            "sector_analysis": ["섹터 분석 단락1", ...],
            "risk_factors": ["리스크 단락1", ...],
            "strategy": ["투자전략 단락1", ...],
            "tomorrow_outlook": ["내일 전망 단락1", ...]
        }
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
    label = "장전" if is_pre else "장후"

    # === HTML 조립 ===
    html = CSS
    html += '<div class="sbv-wrap">'

    # 헤더
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

    # 메트릭 카드
    html += '<div class="sbv-metrics" role="region" aria-label="주요 시장 지표">'
    if is_pre:
        html += metric_card("S&P 500", fmt_num(sp500.get("price", 0), 2), sp500.get("change_pct", 0))
        html += metric_card("NASDAQ", fmt_num(nasdaq.get("price", 0), 2), nasdaq.get("change_pct", 0))
        html += metric_card("KOSPI", fmt_num(kospi.get("price", 0), 2), kospi.get("change_pct", 0))
    else:
        html += metric_card("KOSPI", fmt_num(kospi.get("price", 0), 2), kospi.get("change_pct", 0))
        html += metric_card("KOSDAQ", fmt_num(kosdaq.get("price", 0), 2), kosdaq.get("change_pct", 0))
    html += metric_card("USD/KRW", fmt_num(usdkrw.get("price", 0), 0), usdkrw.get("change_pct", 0), suffix="원")
    html += metric_card("WTI", fmt_num(wti.get("price", 0), 2), wti.get("change_pct", 0), prefix="$")
    html += metric_card("VIX", fmt_num(vix.get("price", 0), 1), vix.get("change_pct", 0))
    html += metric_card("BTC", fmt_num(btc.get("price", 0), 0), btc.get("change_pct", 0), prefix="$")
    html += '</div>'

    # 📌 Executive Summary (핵심 3줄 요약)
    if analysis.get("executive_summary"):
        html += '<div class="sbv-executive"><div class="sbv-executive-title">📌 핵심 요약</div>'
        for i, point in enumerate(analysis["executive_summary"], 1):
            html += f'<div class="sbv-executive-item"><div class="sbv-executive-num">{i}</div><div class="sbv-executive-text">{point}</div></div>'
        html += '</div>'

    # 📰 시황 분석 (AI 내러티브)
    if analysis.get("market_overview"):
        html += analysis_section("📰 시황 분석", analysis["market_overview"])

    # 지수 바 차트
    if is_pre:
        html += '<div class="sbv-section"><div class="sbv-section-title">🇺🇸 미국 시장 지수</div>'
        html += bar_chart_row("S&P 500", sp500.get("price", 0), sp500.get("change_pct", 0))
        html += bar_chart_row("NASDAQ", nasdaq.get("price", 0), nasdaq.get("change_pct", 0))
        html += bar_chart_row("다우존스", dow.get("price", 0), dow.get("change_pct", 0))
        html += '</div>'

    # Mag7 (장전 리포트만 — 장후에는 미장 미개장으로 0%)
    if is_pre:
        html += '<div class="sbv-section"><div class="sbv-section-title">🏢 Magnificent 7</div>'
        for s in us_sorted:
            html += bar_chart_row(s.get("name", ""), s.get("price", 0), s.get("change_pct", 0))
        html += '</div>'

    # 🔍 섹터 분석 (AI 내러티브)
    if analysis.get("sector_analysis"):
        html += analysis_section("🔍 섹터 · 종목 분석", analysis["sector_analysis"])

    # 한국 대표주
    html += '<div class="sbv-section"><div class="sbv-section-title">🇰🇷 한국 대표주</div>'
    for s in kr_sorted:
        html += bar_chart_row(s.get("name", ""), s.get("price", 0), s.get("change_pct", 0))
    html += '</div>'

    # 📊 기술적 분석 (AI 내러티브)
    if analysis.get("technical_levels"):
        html += '<div class="sbv-tech"><div class="sbv-tech-title">📊 기술적 분석</div>'
        for p in analysis["technical_levels"]:
            html += f'<p class="sbv-paragraph">{p}</p>'
        html += '</div>'

    # 💰 자금 흐름 (AI 내러티브)
    if analysis.get("money_flow"):
        html += '<div class="sbv-money"><div class="sbv-money-title">💰 자금 흐름 · 수급 분석</div>'
        for p in analysis["money_flow"]:
            html += f'<p class="sbv-paragraph">{p}</p>'
        html += '</div>'

    # 원자재/환율 테이블
    html += '<div class="sbv-section"><div class="sbv-section-title">💱 원자재 · 환율 · 금리</div>'
    html += '<table class="sbv-table"><thead><tr><th>항목</th><th>가격</th><th>등락</th></tr></thead><tbody>'
    for sym, name in [("KRW=X", "USD/KRW"), ("CL=F", "WTI 원유"), ("GC=F", "금"), ("BTC-USD", "비트코인"), ("^VIX", "VIX"), ("^TNX", "10Y 금리")]:
        c = comm.get(sym, {})
        color = change_color(c.get("change_pct", 0))
        arrow = change_arrow(c.get("change_pct", 0))
        prefix = "$" if sym not in ("KRW=X", "^VIX", "^TNX") else ""
        suffix = "원" if sym == "KRW=X" else "%" if sym == "^TNX" else ""
        html += f'<tr><td>{name}</td><td>{prefix}{fmt_num(c.get("price", 0), 2)}{suffix}</td><td style="color:{color}">{arrow} {abs(c.get("change_pct", 0)):.2f}%</td></tr>'
    html += '</tbody></table></div>'

    # 🔢 오늘의 핵심 숫자 (AI)
    if analysis.get("key_numbers"):
        icons = ["📈", "💹", "🔑", "⚡", "🎯"]
        html += '<div class="sbv-section"><div class="sbv-section-title">🔢 오늘의 핵심 숫자</div>'
        for i, num in enumerate(analysis["key_numbers"]):
            icon = icons[i % len(icons)]
            html += f'<div class="sbv-keynumber"><div class="sbv-keynumber-icon">{icon}</div><div class="sbv-keynumber-text">{num}</div></div>'
        html += '</div>'

    # ⚠️ 리스크 요인 (AI 내러티브)
    if analysis.get("risk_factors"):
        html += analysis_section("⚠️ 리스크 요인", analysis["risk_factors"])

    # 📋 투자 전략 (AI 내러티브)
    if analysis.get("strategy"):
        html += '<div class="sbv-strategy"><div class="sbv-strategy-title">📋 투자 전략</div>'
        for p in analysis["strategy"]:
            html += f'<p>{p}</p>'
        html += '</div>'

    # 🔮 전망 (AI 내러티브 - 강조 스타일)
    if analysis.get("tomorrow_outlook"):
        outlook_title = "오늘 장 전망" if is_pre else "내일 장 전망"
        html += f'<div class="sbv-outlook"><div class="sbv-outlook-title">🔮 {outlook_title}</div>'
        for p in analysis["tomorrow_outlook"]:
            html += f'<p class="sbv-paragraph">{p}</p>'
        html += '</div>'

    html += '<div class="sbv-disclaimer">⚠️ 본 리포트는 투자 참고 자료이며, 투자 판단의 최종 책임은 투자자 본인에게 있습니다. | StockBizView</div>'
    html += '</div>'  # close sbv-wrap

    # 제목 생성 (카테고리 태그 없이 AI 제목 + 날짜)
    if analysis.get("title"):
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

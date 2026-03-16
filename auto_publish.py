"""
StockBizView - 전체 자동화 스크립트
데이터 수집 → AI 분석 → HTML 생성 → WordPress 발행
Cloudways cron 또는 GitHub Actions에서 실행

사용법:
  python auto_publish.py pre_market
  python auto_publish.py post_market
  python auto_publish.py us_market
  python auto_publish.py stock_analysis
  python auto_publish.py investment_strategy
  python auto_publish.py korea_market
"""

import sys
import os
import json
import datetime

# 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
sys.path.insert(0, SCRIPT_DIR)

from collect_data import collect_all, save_json
from generate_report import load_data, generate_report, build_data_summary
from ai_analyst import generate_analysis
from publish_wp import publish_report
from update_homepage import update_homepage
from market_calendar import collect_all_events, build_calendar_html, update_calendar_page

# 리포트 타입 → generate_report의 report_type 매핑
REPORT_TYPE_MAP = {
    "pre_market": "pre",
    "post_market": "post",
    "us_market": "pre",       # 미국 시장은 장전 레이아웃
    "stock_analysis": "post",  # 종목 분석은 장후 레이아웃
    "investment_strategy": "pre",
    "korea_market": "post",
}

# 제목에 카테고리 태그 불필요 (카테고리는 WordPress에서 자동 표시)
# AI가 생성한 제목 + 날짜만 사용


def run(report_type="post_market", status="publish"):
    now = datetime.datetime.now()
    print("=" * 60)
    print(f"  StockBizView Auto Publisher")
    print(f"  Report: {report_type}")
    print(f"  Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: 데이터 수집
    print("\n[1/5] 시장 데이터 수집 중...")
    data = collect_all()
    data_path = os.path.join(SCRIPT_DIR, "latest_market_data.json")
    save_json(data, data_path)

    # Step 2: 홈페이지 실시간 데이터 업데이트
    print("\n[2/5] 홈페이지 실시간 업데이트 중...")
    try:
        update_homepage(data)
    except Exception as e:
        print(f"  ⚠️ 홈페이지 업데이트 실패 (계속 진행): {e}")

    # Step 2.5: 마켓 캘린더 업데이트 (월요일 장전 리포트 시)
    if report_type == "pre_market" and now.weekday() == 0:
        print("\n[2.5/5] 마켓 캘린더 주간 업데이트 중...")
        try:
            events = collect_all_events(weeks_ahead=4)
            cal_html = build_calendar_html(events)
            update_calendar_page(cal_html)
        except Exception as e:
            print(f"  ⚠️ 마켓 캘린더 업데이트 실패 (계속 진행): {e}")

    # Step 3: AI 분석 생성
    print("\n[3/5] AI 애널리스트 분석 생성 중...")
    summary = build_data_summary(data)
    analysis = generate_analysis(summary, report_type)
    print(f"  제목: {analysis.get('title', 'N/A')}")
    print(f"  헤드라인: {analysis.get('headline', 'N/A')[:60]}...")

    # 제목: AI 제목 + 날짜 (카테고리 태그 없이)
    date_display = now.strftime("%Y.%m.%d")
    original_title = analysis.get("title") or f"시장 리포트"

    # Step 4: HTML 리포트 생성
    print("\n[4/5] HTML 리포트 생성 중...")
    layout_type = REPORT_TYPE_MAP.get(report_type, "post")
    title, html = generate_report(data, layout_type, analysis)

    # 최종 제목: AI 헤드라인 + 날짜
    title = f"{original_title} — {date_display}"
    print(f"  최종 제목: {title}")
    print(f"  HTML 크기: {len(html):,} chars")

    # Step 5: WordPress 발행
    print(f"\n[5/5] WordPress 발행 중... (status: {status})")
    result = publish_report(title, html, report_type=report_type, status=status)

    if result:
        print("\n" + "=" * 60)
        print(f"  ✅ 발행 완료!")
        print(f"  📌 Post ID: {result['id']}")
        print(f"  🔗 URL: {result['url']}")
        print(f"  📊 Status: {result['status']}")
        print("=" * 60)

        # 로그 저장
        log_entry = {
            "timestamp": now.isoformat(),
            "report_type": report_type,
            "post_id": result["id"],
            "url": result["url"],
            "title": title,
            "status": result["status"],
        }
        log_path = os.path.join(SCRIPT_DIR, "publish_log.jsonl")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return result


if __name__ == "__main__":
    report_type = sys.argv[1] if len(sys.argv) > 1 else "post_market"
    status = sys.argv[2] if len(sys.argv) > 2 else "publish"

    valid_types = list(REPORT_TYPE_MAP.keys())
    if report_type not in valid_types:
        print(f"Error: Invalid report type '{report_type}'")
        print(f"Valid types: {', '.join(valid_types)}")
        sys.exit(1)

    run(report_type, status)

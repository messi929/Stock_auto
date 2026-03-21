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

# 한국 시간대 (KST = UTC+9)
KST = datetime.timezone(datetime.timedelta(hours=9))

# 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
sys.path.insert(0, SCRIPT_DIR)

from collect_data import collect_all, save_json
from generate_report import load_data, generate_report, build_data_summary
from ai_analyst import generate_analysis
from publish_wp import publish_report, check_today_published
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
    "weekly_recap_kr": "weekly_kr",   # 주말 한국 시장 주간 리뷰
    "weekly_recap_us": "weekly_us",   # 주말 미국 시장 주간 리뷰
}

# 제목에 카테고리 태그 불필요 (카테고리는 WordPress에서 자동 표시)
# AI가 생성한 제목 + 날짜만 사용


def run(report_type="post_market", status="publish"):
    now = datetime.datetime.now(KST)
    print("=" * 60)
    print(f"  StockBizView Auto Publisher")
    print(f"  Report: {report_type}")
    print(f"  Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # WordPress API로 중복 발행 체크
    print("\n[0/5] 중복 발행 체크 중...")
    existing = check_today_published(report_type)
    if existing:
        print(f"\n  ⚠️ 오늘 '{report_type}' 리포트가 이미 발행되었습니다.")
        print(f"  📌 Post ID: {existing.get('post_id')}")
        print(f"  📝 제목: {existing.get('title')}")
        print(f"  🔗 URL: {existing.get('url')}")
        print(f"  ⏭️ 중복 발행을 건너뜁니다.")
        print("=" * 60)
        return None

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
    summary = build_data_summary(data, report_type)
    try:
        analysis = generate_analysis(summary, report_type)
    except Exception as e:
        print(f"  ❌ AI 분석 실패: {e}")
        print(f"  🚫 AI 분석 없이는 발행하지 않습니다.")
        print("=" * 60)
        return None

    # AI 분석 품질 검증
    if not analysis.get("title") or analysis["title"] == "시장 리포트":
        print(f"  ❌ AI 분석 품질 미달 (기본 제목 반환)")
        print(f"  🚫 AI 분석 없이는 발행하지 않습니다.")
        print("=" * 60)
        return None

    # 섹션 완성도 검증 — 최소 4/6 필수 섹션이 있어야 발행
    from ai_analyst import CRITICAL_SECTIONS
    filled = sum(1 for k in CRITICAL_SECTIONS if analysis.get(k))
    min_required = 4
    if filled < min_required:
        print(f"  ❌ AI 분석 섹션 부족 ({filled}/{len(CRITICAL_SECTIONS)}, 최소 {min_required}개 필요)")
        missing = [k for k in CRITICAL_SECTIONS if not analysis.get(k)]
        print(f"  📋 누락: {missing}")
        print(f"  🚫 품질 미달로 발행을 중단합니다.")
        print("=" * 60)
        return None
    print(f"  📊 섹션 검증: {filled}/{len(CRITICAL_SECTIONS)} 필수 섹션 통과")

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
    headline = analysis.get("headline", "")
    result = publish_report(title, html, report_type=report_type, status=status,
                            headline=headline, analysis=analysis)

    if result:
        print("\n" + "=" * 60)
        print(f"  ✅ 발행 완료!")
        print(f"  📌 Post ID: {result['id']}")
        print(f"  🔗 URL: {result['url']}")
        print(f"  📊 Status: {result['status']}")
        print("=" * 60)

        # 로그 출력 (WordPress가 단일 소스, 로컬 파일 불필요)
        print(f"  📋 Report: {report_type} | Post ID: {result['id']}")

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

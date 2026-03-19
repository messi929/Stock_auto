"""
StockBizView - 리포트 자동 발행 스케줄러 데몬

Hetzner 서버에서 systemd 서비스로 실행.
GitHub Actions cron 대체 — 정확한 시각에 발행.

실행 방법:
  python scheduler/stock_runner.py                    # 데몬 모드 (기본)
  python scheduler/stock_runner.py --run pre_market    # 즉시 1회 실행
  python scheduler/stock_runner.py --run homepage      # 홈페이지 업데이트만

스케줄 (KST):
  매일      06:50  장전 리포트
  매일      19:03  장후 리포트
  화/금     09:13  미국 시장
  화/금     19:47  종목 분석
  수        09:07  투자 전략
  월/목     19:33  한국 시장
  30분마다         홈페이지 데이터 업데이트
"""

import sys
import os
import time
import traceback
import datetime

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

import schedule

KST = datetime.timezone(datetime.timedelta(hours=9))
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def log(msg):
    """타임스탬프 포함 로그 출력"""
    now = datetime.datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)

    # 파일 로그
    today = datetime.datetime.now(KST).strftime("%Y-%m-%d")
    log_path = os.path.join(LOG_DIR, f"stock_runner_{today}.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_task(task_name, func, *args):
    """태스크 실행 래퍼 (에러 핸들링 + 로깅)"""
    log(f"▶ {task_name} 시작")
    try:
        result = func(*args)
        log(f"✅ {task_name} 완료")
        return result
    except Exception as e:
        log(f"❌ {task_name} 실패: {e}")
        traceback.print_exc()
        return None


# === 태스크 함수들 ===

def task_publish_report(report_type):
    """리포트 발행"""
    from auto_publish import run
    run_task(f"리포트 발행 [{report_type}]", run, report_type, "publish")


def task_update_homepage():
    """홈페이지 데이터 업데이트"""
    from update_data import run as update_run
    run_task("홈페이지 업데이트", update_run)


# === 요일 체크 헬퍼 ===

def is_weekday(days):
    """현재 요일이 days에 포함되는지 (0=월, 6=일)"""
    return datetime.datetime.now(KST).weekday() in days


def task_if_day(days, report_type):
    """특정 요일에만 실행"""
    if is_weekday(days):
        task_publish_report(report_type)
    else:
        day_names = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
        target = "/".join(day_names[d] for d in days)
        log(f"⏭ {report_type} 스킵 (오늘은 {target}요일 아님)")


# === 스케줄 등록 ===

def setup_schedule():
    """모든 스케줄 등록"""

    # 매일 리포트
    schedule.every().day.at("06:50").do(task_publish_report, "pre_market")
    schedule.every().day.at("19:03").do(task_publish_report, "post_market")

    # 주간 리포트 (요일 체크 포함)
    schedule.every().day.at("09:13").do(task_if_day, [1, 4], "us_market")       # 화/금
    schedule.every().day.at("19:47").do(task_if_day, [1, 4], "stock_analysis")  # 화/금
    schedule.every().day.at("09:07").do(task_if_day, [2], "investment_strategy") # 수
    schedule.every().day.at("19:33").do(task_if_day, [0, 3], "korea_market")    # 월/목

    # 홈페이지 데이터 업데이트 (30분마다)
    schedule.every(30).minutes.do(task_update_homepage)

    log("📋 스케줄 등록 완료:")
    log("  매일   06:50  장전 리포트")
    log("  매일   19:03  장후 리포트")
    log("  화/금  09:13  미국 시장")
    log("  화/금  19:47  종목 분석")
    log("  수     09:07  투자 전략")
    log("  월/목  19:33  한국 시장")
    log("  30분마다      홈페이지 업데이트")


def run_daemon():
    """데몬 모드 — 무한 루프로 스케줄 실행"""
    log("=" * 50)
    log("StockBizView 스케줄러 데몬 시작")
    log(f"프로젝트: {PROJECT_ROOT}")
    log("=" * 50)

    setup_schedule()

    # 시작 직후 홈페이지 업데이트 1회 실행
    task_update_homepage()

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            log(f"❌ 스케줄러 루프 에러: {e}")
            traceback.print_exc()
        time.sleep(30)


def run_once(report_type):
    """단일 태스크 즉시 실행"""
    if report_type == "homepage":
        task_update_homepage()
    else:
        task_publish_report(report_type)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="StockBizView 스케줄러")
    parser.add_argument("--run", type=str, default=None,
                        help="즉시 실행할 태스크 (pre_market, post_market, us_market, "
                             "stock_analysis, investment_strategy, korea_market, homepage)")
    args = parser.parse_args()

    if args.run:
        run_once(args.run)
    else:
        run_daemon()

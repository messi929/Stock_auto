"""
StockBizView - 홈페이지 데이터 자동 갱신 (리포트 발행 없이)
30분마다 시장 데이터를 수집하여 홈페이지 티커바 + Market Pulse 업데이트
"""

import os
import sys
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from collect_data import collect_all
from update_homepage import update_homepage

KST = datetime.timezone(datetime.timedelta(hours=9))


def run():
    now = datetime.datetime.now(KST)
    print(f"[데이터 갱신] {now.strftime('%Y-%m-%d %H:%M:%S')} KST")

    print("  데이터 수집 중...")
    data = collect_all()

    print("  홈페이지 업데이트 중...")
    update_homepage(data)

    print("  ✅ 완료")


if __name__ == "__main__":
    run()

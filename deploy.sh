#!/bin/bash
# StockBizView 서버 배포 스크립트
# 사용법: bash deploy.sh [--setup]  (--setup: 최초 설치)

SERVER=root@77.42.78.9
SERVER_DIR=/opt/stock-auto
SSH_KEY=~/.ssh/id_ed25519
LOCAL_DIR="/c/src/Stock_auto"
TODAY=$(date '+%Y-%m-%d')

echo "=========================================="
echo "  StockBizView 배포"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# === 최초 설치 ===
if [ "$1" = "--setup" ]; then
    echo ""
    echo "[SETUP] 서버 초기 설치 시작..."

    ssh -i "$SSH_KEY" "$SERVER" bash -s << 'SETUP_EOF'
        set -e

        # 디렉토리 생성
        mkdir -p /opt/stock-auto/{scheduler,logs}

        # Python venv 생성
        python3 -m venv /opt/stock-auto/venv
        /opt/stock-auto/venv/bin/pip install --upgrade pip
        /opt/stock-auto/venv/bin/pip install schedule

        echo "✅ 서버 디렉토리 + venv 준비 완료"
SETUP_EOF

    # .env 파일 복사
    echo "[SETUP] .env 파일 복사..."
    scp -i "$SSH_KEY" "$LOCAL_DIR/.env" "$SERVER:$SERVER_DIR/.env"

    # systemd 서비스 등록
    echo "[SETUP] systemd 서비스 등록..."
    scp -i "$SSH_KEY" "$LOCAL_DIR/stock-auto.service" "$SERVER:/etc/systemd/system/stock-auto.service"
    ssh -i "$SSH_KEY" "$SERVER" "systemctl daemon-reload && systemctl enable stock-auto"

    echo "✅ 초기 설치 완료. 이제 'bash deploy.sh'로 코드를 배포하세요."
    exit 0
fi

# === 코드 배포 ===
echo ""
echo "[1/4] Python 소스 코드 배포..."
FILES=(
    "auto_publish.py"
    "ai_analyst.py"
    "collect_data.py"
    "generate_report.py"
    "publish_wp.py"
    "update_homepage.py"
    "update_data.py"
    "update_pages.py"
    "market_calendar.py"
)

for f in "${FILES[@]}"; do
    if [ -f "$LOCAL_DIR/$f" ]; then
        scp -i "$SSH_KEY" "$LOCAL_DIR/$f" "$SERVER:$SERVER_DIR/$f"
    fi
done

echo "[2/4] 스케줄러 배포..."
scp -i "$SSH_KEY" "$LOCAL_DIR/scheduler/stock_runner.py" "$SERVER:$SERVER_DIR/scheduler/stock_runner.py"

echo "[3/4] 서비스 재시작..."
ssh -i "$SSH_KEY" "$SERVER" "systemctl restart stock-auto && sleep 2 && systemctl status stock-auto --no-pager | tail -5"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "  ✅ 배포 완료!"
    echo "  로그: ssh $SERVER 'tail -f /var/log/stock-auto.log'"
    echo "=========================================="
else
    echo ""
    echo "  ❌ 서비스 재시작 실패!"
    exit 1
fi

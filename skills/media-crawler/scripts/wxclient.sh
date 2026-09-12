#!/usr/bin/env bash
# Start/stop/status for the local wx_channels_download proxy used by the wxclient path.
# Starting needs administrator rights (root certificate install + system proxy); run it yourself.
set -euo pipefail
ROOT="${LOV_MEDIA_CRAWLER_CACHE:-$HOME/.cache/lov-media-crawler}/wx_channels_download"
VERSION="v260907"
BIN="$ROOT/$VERSION/wx_video_download"
WORKDIR="$ROOT/workdir"
CONFIG="$WORKDIR/config.yaml"
API="http://127.0.0.1:2022"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<EOF
用法: bash scripts/wxclient.sh <start|status|stop|uninstall-cert>

start           以管理员身份启动本地代理（安装根证书、设置系统代理、监听 127.0.0.1:2023，API 127.0.0.1:2022）
status          检查 API 是否在线、微信视频号页面是否已连接
stop            结束正在运行的代理进程（会恢复系统代理）
uninstall-cert  删除它安装的根证书（需要管理员权限）
EOF
}

require_binary() {
  if [[ ! -x "$BIN" || ! -f "$CONFIG" ]]; then
    echo "尚未安装：先运行  python3 '$SKILL_DIR/scripts/media_crawler.py' setup-wxclient" >&2
    exit 2
  fi
}

cmd="${1:-}"
case "$cmd" in
  start)
    require_binary
    echo "将以管理员身份启动 wx_channels_download $VERSION"
    echo "  工作目录: $WORKDIR"
    echo "  行为: 安装代理根证书、把系统代理指向 127.0.0.1:2023、提供 API $API"
    echo "  结束: 在此终端按 Ctrl+C，系统代理会随之恢复"
    echo "启动后请在微信 PC 端打开任意视频号视频页面并保持打开，再运行下载命令。"
    echo
    exec sudo "$BIN" --workdir "$WORKDIR" -c "$CONFIG"
    ;;
  status)
    if curl -sf --max-time 3 "$API/api/v1/download_task/list?page_size=1" >/dev/null; then
      echo "api: online ($API)"
    else
      echo "api: offline ($API)"; exit 1
    fi
    code="$(curl -s --max-time 10 "$API/api/channels/follow/list" | python3 -c 'import sys,json
try:
    print(json.load(sys.stdin).get("code"))
except Exception:
    print("parse_error")')"
    if [[ "$code" == "0" ]]; then
      echo "wechat channels page: connected"
    else
      echo "wechat channels page: not connected (在微信 PC 端打开任意视频号视频页面)"; exit 3
    fi
    ;;
  stop)
    if pgrep -f "$BIN" >/dev/null; then
      sudo pkill -INT -f "$BIN" && echo "已发送停止信号"
    else
      echo "没有运行中的进程"
    fi
    ;;
  uninstall-cert)
    require_binary
    exec sudo "$BIN" uninstall
    ;;
  *)
    usage; exit 1
    ;;
esac

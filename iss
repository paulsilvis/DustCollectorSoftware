#!/bin/bash

# ISS Feed Control Script

SERVICE_NAME="iss-feed.service"

case "$1" in
    start)
        echo "Starting ISS feed..."
        sudo systemctl start "$SERVICE_NAME"
        ;;
    stop)
        echo "Stopping ISS feed..."
        sudo systemctl stop "$SERVICE_NAME"
        ;;
    restart)
        echo "Restarting ISS feed..."
        sudo systemctl restart "$SERVICE_NAME"
        ;;
    status)
        sudo systemctl status "$SERVICE_NAME"
        ;;
    enable)
        echo "Enabling ISS feed to start on boot..."
        sudo systemctl enable "$SERVICE_NAME"
        ;;
    disable)
        echo "Disabling ISS feed from starting on boot..."
        sudo systemctl disable "$SERVICE_NAME"
        ;;
    logs)
        echo "Showing recent logs..."
        sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager
        ;;
    tail)
        echo "Tailing logs (Ctrl-C to exit)..."
        sudo journalctl -u "$SERVICE_NAME" -f
        ;;
    *)
        echo "ISS Feed Control"
        echo "Usage: iss {start|stop|restart|status|enable|disable|logs|tail}"
        echo ""
        echo "  start    - Start the ISS feed"
        echo "  stop     - Stop the ISS feed"
        echo "  restart  - Restart the ISS feed"
        echo "  status   - Show service status"
        echo "  enable   - Enable auto-start on boot"
        echo "  disable  - Disable auto-start on boot"
        echo "  logs     - Show recent log entries"
        echo "  tail     - Follow log output in real-time"
        exit 1
        ;;
esac

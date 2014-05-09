#!/bin/sh

pidfile=/var/run/launcher.pid
pidsreset=/var/run/sketch_reset.pid
launcher=/opt/cln/galileo/launcher.sh
sreset=/opt/cln/galileo/galileo_sketch_reset

start_handler()
{
    type dmidecode > /dev/null 2>&1 || die "dmidecode not installed"
    board=$(dmidecode -s baseboard-product-name)
    case "$board" in *"Galileo" ) start_galileod ;; esac
}

start_galileod()
{
    echo "Starting galileod"
    start-stop-daemon -q -S -m -p $pidfile -b -x $launcher
    start-stop-daemon -q -S -m -p $pidsreset -b -x $sreset
}

stop_handler()
{
    echo "Stopping galileod"
    start-stop-daemon -q -K -p $pidfile -s USR1
    start-stop-daemon -q -K -p $pidsreset
    rm $pidfile -f
    rm $pidsreset -f
}

die()
{
    exit 1
}

case "$1" in
  start)
        start_handler
        ;;
  stop)
        stop_handler
        ;;
  restart)
        $0 stop
        $0 start
        ;;
  *)
        echo "Usage: syslog { start | stop | restart }" >&2
        exit 1
        ;;
esac

exit 0


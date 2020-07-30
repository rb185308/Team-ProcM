#!/bin/bash
start() {
bash /home/app/procAlive/daemon.sh &
}

stop() {
PID=`ps -eaf | grep daemon.sh | grep -v grep | awk -F" " '{print $2}'`
kill -n 9 $PID
}

status() {
PID=`ps -eaf | grep daemon.sh | grep -v grep | awk -F" " '{print $2}'`
if [ -z "$PID" ] 
then
echo "procAlived is not running"
else
echo "procAlived is running"
fi
}

case "$1" in
  start)
	start
        status
	;;
  stop)
       stop
       status
       ;;
  status)
        status
        ;;
  restart)
        stop
        status
        start
        status
        ;;
  *)
	echo $"Usage: $prog {start|stop|restart|status}"
	exit 1
esac

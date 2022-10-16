#!/bib/bash
COUNT=0
for i in $(ls /sys/bus/usb/devices/) ; do
	COUNT=$((COUNT+1))
	udevadm info /sys/bus/usb/devices/$i | grep -i driver

done
echo $COUNT

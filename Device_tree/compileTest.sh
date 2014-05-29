dtc -O dtb -o /lib/firmware/BB-TEST-00A0.dtbo -b 0 -@ BB-BONE-REPLICAP-00A3.dts
echo "BB-TEST" > /sys/devices/bone_capemgr.*/slots
cat /sys/kernel/debug/pinctrl/44e10800.pinmux/pingroups

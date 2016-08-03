#!/bin/bash

programDir=`dirname $0`
programDir=$(readlink -f $programDir)

usage()
{
    echo "sh `basename $0`  osDisk  IP_ex  IP_admin  IP_vm"

}


function safe_exit()
{
    sleep 1
    umount $1
    if [ "$?" != "0" ]; then
        sleep 2
        umount $1
    fi
    exit 2
}



set -x


[ "$1" ] || { usage; exit 1; }
[ "$2" ] || { usage; exit 1; }
[ "$3" ] || { usage; exit 1; }
[ "$4" ] || { usage; exit 1; }

osDisk="$1"
IP_ex="$2"
IP_admin="$3"
IP_vm="$4"


if ! [ -f ${osDisk} ]; then
    echo "Error: ${osDisk} is not a file!"
    exit 1
fi


diskBaseName=`basename $osDisk`
vmName=`echo ${diskBaseName} | cut -d . -f 1`

if virsh list | grep ${vmName} ; then
    echo "Error: vm ${vmName} not still running! Please shut it down."
    exit 1
fi



guestmountDir="/mnt/guestmount_${diskBaseName}_$(date '+%Y%m%d-%H%M%S')"
mkdir -p ${guestmountDir} || exit 1
guestmount -a  ${osDisk} -i --rw ${guestmountDir} || exit 1


## network config
cat > ${guestmountDir}/etc/sysconfig/network-scripts/ifcfg-eth0 << EOF
DEVICE=eth0
NAME=eth0
TYPE=Ethernet
ONBOOT=yes
BOOTPROTO=static
IPADDR=${IP_ex}
PREFIX=26
GATEWAY=65.255.36.190
DNS1=8.8.8.8
EOF

cat > ${guestmountDir}/etc/sysconfig/network-scripts/ifcfg-eth1 << EOF
DEVICE=eth1
NAME=eth1
TYPE=Ethernet
ONBOOT=yes
BOOTPROTO=static
IPADDR=${IP_admin}
PREFIX=24
EOF

cat > ${guestmountDir}/etc/sysconfig/network-scripts/ifcfg-eth2 << EOF
DEVICE=eth2
NAME=eth2
TYPE=Ethernet
ONBOOT=yes
BOOTPROTO=static
IPADDR=${IP_vm}
PREFIX=24
MTU=1600
EOF



## console
sed -i '/linux16 /s/console=tty0//g' ${guestmountDir}/boot/grub2/grub.cfg  && \
sed -i '/linux16 /s/console=ttyS0,115200//g' ${guestmountDir}/boot/grub2/grub.cfg  && \
sed -i '/linux16 /s/$/ console=tty0 console=ttyS0,115200/g' ${guestmountDir}/boot/grub2/grub.cfg 


## ssh key
rm -f ${guestmountDir}/etc/ssh/ssh_host_*


## hostname
echo ${IP_ex} | sed -e 's/\./_/g' > ${guestmountDir}/etc/hostname
cat ${guestmountDir}/etc/hostname


sleep 1
umount ${guestmountDir}
if [ "$?" != "0" ]; then
    sleep 2
    umount ${guestmountDir} || exit 3
fi

exit 0








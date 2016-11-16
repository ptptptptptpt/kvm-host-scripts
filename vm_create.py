#!/usr/bin/python

import sys
import commands
import os
import time
import random
import getopt
import uuid as UUID



def func_usage():
    print '''
    Usage:
        python vm_create.py -n VM_NAME -c N -m N --osdisk=FILE  [-C yes]  [--vnc=no] [-u UUID]
        python vm_create.py --name=VM_NAME --cpu=N --mem=N --osdisk=FILE  [--cdrom=yes]  [--vnc=no] [--uuid=UUID]

'''


def calc_vnc_port(VM_NAME):
    zeroToNine = [ '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',  ]
    if VM_NAME[-1] in zeroToNine   and   VM_NAME[-2] in zeroToNine:
        portOffset = int(VM_NAME[-2:])
    else:
        portOffset = sum([ ord(eachChar) for eachChar in VM_NAME ]) % 100 + 100
    thePort = 5900 + portOffset
    print 'INFO: VNC port is %s.' % thePort
    return thePort


def define_vm_kvm():
    ##### base #####
    vmCfgXml = '''
<domain type='kvm'>
  <name>%s</name>
  <uuid>%s</uuid>
  <memory>%s</memory>
  <currentMemory>%s</currentMemory>
  
  <vcpu cpuset="%s">%s</vcpu>
  
  <os>
    <type arch='x86_64' machine='pc-i440fx-rhel7.0.0'>hvm</type>
    <boot dev='hd'/>
  </os>
  
  <features>
    <acpi/>
    <apic/>
    <pae/>
  </features>
  
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
'''%(vmName, theUUID, int(float(mem)*1024*1024), int(float(mem)*1024*1024), cpuSet, cpu)

    ##### cpu topology #####
    topoStr = ''
    if cpu == '2':
        topoStr = "<topology sockets='1' cores='1' threads='2'/>"
    elif cpu == '4':
        topoStr = "<topology sockets='1' cores='2' threads='2'/>"
    elif cpu == '6':
        topoStr = "<topology sockets='1' cores='3' threads='2'/>"
    elif cpu == '8':
        topoStr = "<topology sockets='2' cores='2' threads='2'/>"
    elif cpu == '12':
        topoStr = "<topology sockets='2' cores='3' threads='2'/>"
    elif cpu == '16':
        topoStr = "<topology sockets='2' cores='4' threads='2'/>"

    if topoStr:
        vmCfgXml += '''
  <cpu>
    %s
  </cpu> '''%topoStr

    ##### clock #####
    vmCfgXml += '''
  <clock offset='utc'/> '''

    ##### devices #####
    vmCfgXml += '''
  <devices>
    <emulator>/usr/libexec/qemu-kvm</emulator> '''

    ### osdisk ###
    diskCfg = '''
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='none' io='native'/>
      <source file='%s'/>
      <target dev='vda' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
    </disk>''' % osdisk
    vmCfgXml += diskCfg

    ### interfaces ###
    vmCfgXml += '''
    <interface type='bridge'>
      <mac address='%s'/>
      <source bridge='%s'/>
      <virtualport type='openvswitch' />
      <model type='virtio'/>
      <driver name='qemu' event_idx='off'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
    </interface>'''%(MAC0, BR0)

    vmCfgXml += '''
    <interface type='bridge'>
      <mac address='%s'/>
      <source bridge='%s'/>
      <model type='virtio'/>
      <driver name='qemu' event_idx='off'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x08' function='0x0'/>
    </interface>'''%(MAC1, BR1)

    ###
    vmCfgXml += '''
    <serial type='pty'>
      <target port='0'/>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console> '''

    ### vnc ###
    if vnc == 'no' :
        pass
    else:
        videoType = ''
        if virtType == "para" :
            videoType = 'cirrus'
        elif virtType == "hvm" :
            videoType = 'vga'
        vncPort = calc_vnc_port(vmName)
        vncPasswd = str(UUID.uuid4()).replace('-', '')[-8:]
        vmCfgXml += '''
    <input type='tablet' bus='usb'/>
    <input type='mouse' bus='ps2'/>
    <graphics type='vnc' port='%s' passwd='%s' />
    <video>
      <model type='%s' vram='4096' heads='1'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
    </video> '''%(vncPort, vncPasswd, videoType)
    #<graphics type='vnc' port='-1' autoport='yes'/>

    ### memballoon ###
    vmCfgXml += '''
    <memballoon model='virtio'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
    </memballoon> ''' 

    ### cdrom ###
    if cdrom == 'yes':
        vmCfgXml += '''
    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw' cache='none' io='native'/>
      <source file='/root/test-kvm/CentOS-7-x86_64-Minimal.iso'/>
      <target dev='sdr0' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>
    </disk>'''

    ### end ###
    vmCfgXml += '''
  </devices>
</domain> \n'''

    tmpCfgFile = '/tmp/kvm_vm_%s_%s.xml'%(vmName, theUUID)

    f = file(tmpCfgFile, 'w')
    f.write(vmCfgXml)
    f.close()

    cmd = 'virsh define %s' % tmpCfgFile
    status, ret = commands.getstatusoutput(cmd)
    if status != 0:
        print 'Error: %s failed !' % cmd
        print ret
        raise Exception, 'Error: %s failed !' % cmd

    cmd= 'virsh autostart %s'%vmName
    status, ret=commands.getstatusoutput(cmd)
    if status != 0:
        print 'Error: %s failed !' % cmd
        print ret
        raise Exception, 'Error: %s failed !' % cmd



if __name__ == '__main__':
    vmName = ''
    cpu = ''
    mem = ''
    osdisk = ''
    vnc = ''
    uuid = ''
    cdrom = ''

    datadisk = ''

    opts, args = getopt.getopt(sys.argv[1:], "hn:c:m:u:C:", ["help", "output=", "name=", 'cpu=', 'mem=', 'osdisk=', 'vnc=', 'uuid=', 'cdrom='])
    for opt, arg in opts:  
        if opt in ("-h", "--help"):  
            func_usage()
            sys.exit(1)
        elif opt in ("-n", "--name"):  
            vmName = arg
        elif opt in ("-c", "--cpu"):  
            cpu = arg
        elif opt in ("-m", "--mem"):  
            mem = arg
        elif opt in ("--osdisk", ):  
            osdisk = arg
        elif opt in ("--vnc", ):  
            vnc = arg
        elif opt in ("-u", "--uuid"):  
            uuid = arg
        elif opt in ("-C", "--cdrom"):  
            cdrom = arg
        else:  
            print "Invalid argument: %s ==> %s" %(opt, arg)
            func_usage()
            sys.exit(1)

    errMsgList = []
    if not vmName:
        errMsgList.append('Error: name is not set!')
    if not cpu:
        errMsgList.append('Error: cpu is not set!')
    if not mem:
        errMsgList.append('Error: mem is not set!')
    if not osdisk:
        errMsgList.append('Error: osdisk is not set!')

    if errMsgList:
        print '\n'.join(errMsgList)
        func_usage()
        sys.exit(1)



    # check vmNAME 
    cmd = 'virsh dominfo %s'%vmName
    status, ret = commands.getstatusoutput(cmd)
    if status == 0:
        raise Exception, 'Error: VM %s already exists!'%vmName



    # generate vif MAC 
    MAC = [ 0xaa, 0xaa, 0xaa, random.randint(0x00, 0x7f), random.randint(0x00, 0xff), random.randint(0x00, 0xf0) ]
    MAC0 = ':'.join(map(lambda x: "%02x" % x, MAC))
    
    MAC[5] += 1
    MAC1 = ':'.join(map(lambda x: "%02x" % x, MAC))
    
    MAC[5] += 1
    MAC2 = ':'.join(map(lambda x: "%02x" % x, MAC))
    
    print '\n'.join([MAC0, MAC1, MAC2])

    BR0 = 'br-ex'
    BR1 = 'br_enp6s0'

    # generate uuid
    if uuid:
        theUUID = uuid
    else:
        theUUID = str(UUID.uuid4())
    print theUUID

    # cpuSet
    cpuSet = '4-31'

    ## virt type
    virtType = "para" 

    ### create it ! ###
    define_vm_kvm()

    print "VM %s created successfully !" % vmName





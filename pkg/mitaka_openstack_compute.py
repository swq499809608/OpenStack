#!/usr/bin/env python
#-*-coding:UTF-8-*-
"""
@Item   :  Install Openstack Compute
@Author :  william
@Group  :  Network System Group
@Date   :  2014-03-20
@Funtion:gg
    Function: Depoly Openstack Compute  ...
"""
import os,sys,time
import traceback,shutil
import commands
import re

def LOG(info):
    logfile = '/tmp/openstack_compute_install.log'
    files = open(logfile,'a')
    try:
        files.write('%s : %s'%(time.ctime(),info))
    except IOError:
        files.close()
    files.close()

class DepolyCompute(object):
    def __init__(self):
        print "Please write in the script master IP public IP and local management ... \n"
        self.masterIPaddr = '10.0.1.2'
        self.localIPaddr  = '10.0.1.5'
        self.nova_path  = '/etc/nova/'
        self.secret = "7efe56e5-b651-4816-a4e7-1e733a7ebedb"
        self.URL = 'http://%s/source/'%self.masterIPaddr
        self.URL = 'http://%s:8080/source/' %self.masterIPaddr

    def install_packstack(self):
        yum_path = '/etc/yum.repos.d/'
        try:
            cmd = "yum install -y https://rdoproject.org/repos/rdo-release.rpm"
            x,y = commands.getstatusoutput(cmd)
            if x != 0:
                fp = open('%s/rdo-release.repo'%yum_path,'w')
                fp.write("""[openstack-mitaka] \n""")
                fp.write("""name=OpenStack Mitaka Repository \n""")
                fp.write("""baseurl=http://mirror.centos.org/centos/7/cloud/$basearch/openstack-mitaka/ \n""")
                fp.write("""enabled=1 \n""")
                fp.write("""gpgcheck=1 \n""")
                fp.write("""gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-SIG-Cloud \n""")
                fp.close()
        except:
            LOG(traceback.format_exc())

    def install_kvm_compute(self):
        try:
            os.system(""" yum -y install kvm libvirt qemu virt-* python-rbd  """)
            os.system(""" yum -y install openstack-cinder""")
            os.system(""" yum -y install lrzsz gcc sysstat net-snmp-* """)
            os.system(""" yum -y install openstack-nova-compute openstack-nova-network libguestfs-winsupport""")
            ip = self.localIPaddr.split('.')
            os.system("easy_install psutil")
            os.system("easy_install ipdb")
        except:
            LOG(traceback.format_exc())

    def install_compute_source(self):
        try:
            cmd = " wget %s/athCloudOpenStack.tgz  -O /opt/athCloudOpenStack.tgz"%self.URL
            x,y = commands.getstatusoutput(cmd)
            if x == 0:
                os.chdir('/opt/')
                os.system(""" tar -xzvf athCloudOpenStack.tgz -C /""")
                os.chdir(self.nova_path)
                if os.path.exists('nova.conf'):
                    shutil.move('nova.conf','nova.conf.default')
                if os.path.exists('nova.conf.example'):
                    shutil.move('nova.conf.example','nova.conf')
                    self._nova_config()
                self._start_nova_compute()
            else:
                LOG("wget athCloudOpenStack.tgz false")
                sys.exit()
        except:
            LOG(traceback.format_exc())

    def _start_nova_compute(self):
        try:
            servers = ['openstack-nova-compute','openstack-nova-network','libvirtd','openstack-cinder-volume']
            for i in servers:
                os.system(""" systemctl enable %s.service """ %i)
        except:
            LOG(traceback.format_exc())

    def _nova_config(self):
        # Compute node nova.conf init
        try:
            fp = open('%s/nova.conf'%self.nova_path)
            f = fp.readlines()
            fp.close()
            for n, s in enumerate(f):
                if re.match('#?glance_api_servers.*',s):
                    f[n] = 'glance_api_servers=%s:9292\n' %self.masterIPaddr
                if re.match('#?metadata_host.*',s):
                    f[n] = 'metadata_host=%s  \n' %self.masterIPaddr
                if re.match('#?qpid_hostname.*',s):
                    f[n] = 'qpid_hostname=%s\n' %self.masterIPaddr
                if re.match('#?novncproxy_base_url.*',s):
                    f[n] = 'novncproxy_base_url=http://%s:6080/vnc_auto.html \n' %self.masterIPaddr
                if re.match('#?sql_connection.*',s):
                    str = s.split('@')[0] + '@%s/nova'%self.masterIPaddr
                    f[n] = '%s \n' %str
                if re.match('#?my_ip.*',s):
                    f[n] = 'my_ip=%s\n' %self.localIPaddr
                if re.match('#?vncserver_listen.*',s):
                    f[n] = 'vncserver_listen=%s\n' %self.localIPaddr
                if re.match('#?vncserver_proxyclient_address.*',s):
                    f[n] = 'vncserver_proxyclient_address=%s\n' %self.localIPaddr
            fp = open('%s/nova.conf'%self.nova_path,'w')
            fp.writelines(f)
            fp.close()
        except Exception,e:
            LOG(traceback.format_exc())
    
    def cinder_init(self):
        try:
            os.system(""" service libvirtd restart  """)
            os.system(""" scp -P 30000 %s:/etc/ceph/*  /etc/ceph/ """ %self.masterIPaddr)
            os.system("""cd /etc/ceph/  """)
            os.system("""virsh secret-define --file /etc/ceph/secret.xml """)
            os.system("""sudo chown cinder:cinder /etc/ceph/ceph.client.cinder.keyring """)
            os.system("""sudo chown cinder:cinder /etc/ceph/ceph.client.cinder-backup.keyring """)
            os.system("""sudo virsh secret-set-value --secret %s --base64 $(cat /etc/ceph/client.cinder.key) """ %self.secret)
        except:
            print traceback.format_exc()
            LOG(traceback.format_exc())

if __name__ == "__main__":
    sc = DepolyCompute()
    sc.install_packstack()
    sc.install_kvm_compute()
    sc.install_compute_source()
    sc.cinder_init()

# Install Mitaka OpenStack 

##一. OpenStack（Mitaka）环境部署 

1. 安装rdo release 包 

		yum install -y https://www.rdoproject.org/repos/rdo-release.rpm
		yum update -y
        reboot 
		yum install -y openstack-packstack

2. 编辑 puppet Error 

		vim /usr/lib/python2.7/site-packages/packstack/modules/puppet.py 107 
         89             for regex, surrogate in surrogates:
         90                 match = re.search(regex, error)
         91                 if match is None:
         92                     continue
         93 
         94                 args = {}
         95                 num = 1
         96                 while True:
         97                     try:
         98                         args['arg%d' % num] = match.group(num)
         99                         num += 1
        100                     except IndexError:
        101                         break
        102                 error = surrogate % args
        103 
        104             #message = ('Error appeared during Puppet run: %s\n%s\n'
        105             #           'You will find full trace in log %s' %
        106             #           (manifestfile, error, logpath))
        107             #raise PuppetError(message)
        
3. 安装 OpenStack 

		packstack --os-heat-install=y --os-neutron-install=n --os-swift-install=n --nagios-install=n --os-heat-install=y --os-trove-install=y --os-heat-cloudwatch-install=y --os-heat-cfn-install=y --allinone
        
4. 禁止 firewalld 服务 

		systemctl disable firewalld
		systemctl stop firewalld
		systemctl disable NetworkManager
		systemctl stop NetworkManager
		systemctl enable network
		systemctl start network
        
5. 登录dashboard 

		http://127.0.0.1
        
6. 设置nova-network 

		1. 修改rootwarp 用户读取权限 
			 chown nova:nova -R /usr/share/nova/*

		2. 修改/etc/nova.conf 为VLANMange 模式 
			vim /etc/nova/nova.conf
            	network_manage = network_manager=nova.network.manager.VlanManager
                
		3. 修改Nova-network 启动用户进程 
            cat /usr/lib/systemd/system/openstack-nova-network.service 
            [Unit]
            Description=OpenStack Nova Network Server
            After=syslog.target network.target

            [Service]
            Type=notify
            NotifyAccess=all
            TimeoutStartSec=0
            Restart=always
            User=root
            ExecStart=/usr/bin/nova-network

            # Don't kill dnsmasq on shutdown (#805947)
            KillMode=process

            [Install]
            WantedBy=multi-user.target
            
		4.启动Nova-network 服务 
			systemctl enable openstack-nova-network
            systemctl restart openstack-nova-netwrk 
            
		5. 创建nova-network 
			nova-manage network create publics --fixed_range_v4=10.0.1.0/24 --num_networks=1 --network_size=256  --bridge_interface=bond0 --multi_host=T --project_id=7b98a7afb66542c7874ddec80******* --bridge=br100
            
		6. 创建VM
			登录dashboard ，创建VM 
            
##二. Ceph 整合 Nova,Glance,Cinder 

![](../image/ops_ceph.png) 

1. 创建nova,cinder,glance pool(Ceph Cluster 操作) 

		ceph osd pool create volumes 500
        ceph osd pool create images 500
        ceph osd pool create backups 500
        ceph osd pool create instances 500
        PG = OSD*100/3 #osd*60*100/3 = 2000/4
        
2. OpenStack Controller 基础包安装（Mitaka)  
	
    	1. 安装ceph  rbd 
    		yum -y install ceph python-rbd

3. 设置 Ceph用户权限 

		1. ceph auth get-or-create client.cinder mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=volumes, allow rwx pool=instances, allow rx pool=images'
    	
        2. ceph auth get-or-create client.glance mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=images'
    	
        3.ceph auth get-or-create client.cinder-backup mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=backups'

4. 添加keyring 到glance, cinder,nova 

      	1. ceph auth get-or-create client.glance | sudo tee /etc/ceph/ceph.client.glance.keyring
        sudo chown glance:glance /etc/ceph/ceph.client.glance.keyring

       	2. ceph auth get-or-create client.cinder |sudo tee /etc/ceph/ceph.client.cinder.keyring
        sudo chown cinder:cinder /etc/ceph/ceph.client.cinder.keyring
		(计算节点获取keyring)
        
       	3. ceph auth get-or-create client.cinder-backup | sudo tee /etc/ceph/ceph.client.cinder-backup.keyring
        sudo chown cinder:cinder /etc/ceph/ceph.client.cinder-backup.keyring
        
       	4. ceph auth get-key client.cinder |   tee client.cinder.key

5. libvirt ceph 配置（计算节点） 

     	1.生成 UUID 
     		uuidgen
       
       	2. 生成 secret 文件 
            cat > secret.xml <<EOF
            <secret ephemeral='no' private='no'>
              <uuid>7efe56e5-b651-4816-a4e7-1e733a7ebedb</uuid>
              <usage type='ceph'>
                <name>client.cinder secret</name>
              </usage>
            </secret>
            EOF

       	3.定义 secret file  
       		virsh secret-define --file secret.xml
           	sudo virsh secret-set-value --secret 7efe56e5-b651-4816-a4e7-1e733a7ebedb --base64 $(cat client.cinder.key) 

6. Glance api 配置 
		
		[root@l22-250-2 glance]# cat glance-api.conf |grep -v '^$'|grep -v '^#'|grep rbd
        store = rbd
        default_store = rbd
        rbd_store_chunk_size = 8
        rbd_store_pool = images
        rbd_store_user = glance
        rbd_store_ceph_conf = /etc/ceph/ceph.conf
        
7. Cinder api 配置 
		
        [DEFAULT]
        backup_ceph_conf = /etc/ceph/ceph.conf
        backup_driver = cinder.backup.drivers.ceph
        backup_ceph_user = cinder
        backup_ceph_chunk_size = 134217728
        backup_ceph_pool = backups
        backup_ceph_stripe_unit = 0
        backup_ceph_stripe_count = 0
        restore_discard_excess_bytes = true
        glance_host = 10.0.1.2
        enable_v1_api = True
        enable_v2_api = True
        enable_v3_api = True
        storage_availability_zone = nova
        default_availability_zone = nova
        auth_strategy = keystone
        enabled_backends = ceph
        osapi_volume_listen = 0.0.0.0
        osapi_volume_workers = 32
        rbd_pool = images
        rbd_user = cinder
        rbd_ceph_conf =/etc/ceph/ceph.conf
        rbd_flatten_volume_from_snapshot = false
        rbd_secret_uuid = 7efe56e5-b651-4816-a4e7-1e733a7ebedb
        rbd_max_clone_depth = 5
        rbd_store_chunk_size = 4
        nova_catalog_info = compute:nova:publicURL
        nova_catalog_admin_info = compute:nova:adminURL
        debug = False
        verbose = True
        log_dir = /var/log/cinder
        rpc_backend = rabbit
        control_exchange = openstack
        api_paste_config = /etc/cinder/api-paste.ini
        notification_driver=messagingv2
        [BACKEND]
        [BRCD_FABRIC_EXAMPLE]
        [CISCO_FABRIC_EXAMPLE]
        [COORDINATION]
        [FC-ZONE-MANAGER]
        [KEYMGR]
        [cors]
        [cors.subdomain]
        [database]
        connection = mysql+pymysql://cinder:1asdfasdfasdfasdfasdf1@10.0.1.2/cinder
        [keystone_authtoken]
        auth_uri = http://10.0.1.2:5000/v2.0
        admin_password=3a63f5c3604344a7
        admin_tenant_name=services
        identity_uri=http://10.0.1.2:35357
        admin_user=cinder
        [matchmaker_redis]
        [oslo_concurrency]
        lock_path = /var/lib/cinder/tmp
        [oslo_messaging_amqp]
        [oslo_messaging_notifications]
        [oslo_messaging_rabbit]
        amqp_durable_queues = False
        kombu_ssl_keyfile =
        kombu_ssl_certfile =
        kombu_ssl_ca_certs =
        rabbit_host = 10.22.250.2
        rabbit_port = 5672
        rabbit_hosts = 10.22.250.2:5672
        rabbit_use_ssl = False
        rabbit_userid = guest
        rabbit_password = guest
        rabbit_virtual_host = /
        rabbit_ha_queues = False
        heartbeat_timeout_threshold = 0
        heartbeat_rate = 2
        [oslo_middleware]
        [oslo_policy]
        [oslo_reports]
        [oslo_versionedobjects]
        [ssl]

        [ceph]
        volume_driver = cinder.volume.drivers.rbd.RBDDriver
        rbd_pool = volumes
        rbd_ceph_conf = /etc/ceph/ceph.conf
        rbd_flatten_volume_from_snapshot = false
        rbd_max_clone_depth = 5
        rbd_store_chunk_size = 4
        rados_connect_timeout = -1
        glance_api_version = 2
        rbd_secret_uuid = 7efe56e5-b651-4816-a4e7-1e733a7ebedb
          
8. Nova compute 配置 

	1. libvirtd Cache 配置 
            vim /etc/ceph/ceph.conf 
            [client]
            rbd cache = true
            rbd cache writethrough until flush = true
            admin socket = /var/run/ceph/guests/$cluster-$type.$id.$pid.$cctid.asok
            log file = /var/log/qemu/qemu-guest-$pid.log
            rbd concurrent management ops = 20
	
	2. nova.conf 配置 
			....
            
9.Glange 上传镜像 

10. Cinder 用户权限 

##四.  Compute 计算节点安装程序 

1. 计算节点 

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

##三. 参考文献
1.  http://docs.ceph.com/docs/master/rbd/rbd/ 


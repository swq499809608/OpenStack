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
	

##三. 参考文献
1.  http://docs.ceph.com/docs/master/rbd/rbd/ 


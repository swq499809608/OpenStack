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


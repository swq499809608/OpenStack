#/usr/bin/env bash


rm -frv /var/lib/ceph/bootstrap-osd/*
rm -frv /var/lib/ceph/osd/*
rm -frv /data1/* /data2/* /data3/* /data4/* /data5/*  /data6/* /data7/* /data8/* /data9/* /data10/* /data11/* /data12/*


cd /etc/ceph/
#scp -P 30000 10.0.1.2:/etc/ceph/*  /etc/ceph/


chown ceph:ceph /data*

ceph-deploy --overwrite-conf  osd prepare `hostname`:/data1
ceph-deploy --overwrite-conf  osd prepare `hostname`:/data2
ceph-deploy --overwrite-conf  osd prepare `hostname`:/data4
ceph-deploy --overwrite-conf  osd prepare `hostname`:/data3
ceph-deploy --overwrite-conf  osd prepare `hostname`:/data5
ceph-deploy --overwrite-conf  osd prepare `hostname`:/data6
ceph-deploy --overwrite-conf  osd prepare `hostname`:/data7
ceph-deploy --overwrite-conf  osd prepare `hostname`:/data8
ceph-deploy --overwrite-conf  osd prepare `hostname`:/data9
ceph-deploy --overwrite-conf  osd prepare `hostname`:/data10
ceph-deploy --overwrite-conf  osd prepare `hostname`:/data11
ceph-deploy --overwrite-conf  osd prepare `hostname`:/data12

ceph-deploy  --overwrite-conf osd activate `hostname`:/data1
ceph-deploy  --overwrite-conf osd activate `hostname`:/data2
ceph-deploy  --overwrite-conf osd activate `hostname`:/data4
ceph-deploy  --overwrite-conf osd activate `hostname`:/data3
ceph-deploy  --overwrite-conf osd activate `hostname`:/data5
ceph-deploy  --overwrite-conf osd activate `hostname`:/data6
ceph-deploy  --overwrite-conf osd activate `hostname`:/data7
ceph-deploy  --overwrite-conf osd activate `hostname`:/data8
ceph-deploy  --overwrite-conf osd activate `hostname`:/data9
ceph-deploy  --overwrite-conf osd activate `hostname`:/data10
ceph-deploy  --overwrite-conf osd activate `hostname`:/data11
ceph-deploy  --overwrite-conf osd activate `hostname`:/data12

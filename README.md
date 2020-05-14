# Publishing

If you publish an academic paper using the results of the 5GIIK-testbed, please cite:

Ali Esmaeily, Katina Kralevska, and Danilo Gligoroski. "A Cloud-based SDN/NFV Testbed for End-to-End Network Slicing in 4G/5G." arXiv preprint arXiv:2004.10455 (2020). https://arxiv.org/abs/2004.10455

# 5GIIK-testbed

This GitHub repository includes the main procedures to deploy 5GIIK testbed for Network Slicing and Orchestration.
5GIIK is an academic platform has been created in the information security department of NTNU university in Norway. 

# Testbed Architecture

5GIIK emulates 4G/5G networks by utilizing 
* OpenAirInterface (OAI) EPC or NetxtEPC as Core Network (CN)
* Software Radio Systems (SRS) LTE as Radio Access Network (RAN)
* Open-Source MANO (OSM) as a service orchestrator 
* OpenStack as Virtualized Infrastructure Manager (VIM)
* 5G-EmPOWER and ONOS SDN controllers for various network domains.

# Service Orchestrator Deployment (Open-Source Mano (OSM))

You need to have an Ubuntu18.04 (64-bit variant required) system with 2 CPUs, 8 GB RAM, at least 40GB disk, and a single interface with Internet access for deploying OSM release 7. It is recommended to install the OSM with debugging capabilities.

```
wget https://osm-download.etsi.org/ftp/osm-7.0-seven/install_osm.sh
chmod +x install_osm.sh
./install_osm.sh 2>&1 | tee osm_install_log.txt
```

You can then check if the installation has been done correctly with the following commands.

```
docker stack ps osm |grep -i running
docker service ls
```

Simply navigate to the OSM GUI by accessing the IP address of your host machine and using "admin/admin" as OSM credentials. For accessing the OSM installed on a remote machine, execute the following command on your main host.

```
sudo apt-get install openssh-server
service ssh status
```

# Virtualized Infrastructure Manager (VIM) deployment (OpenStack)

In the following, the procedures of deploying all-in-one openstack implementation are explained. First prepare a server with the minimum requirements such as at least 64GB of RAM, 100GB of storage, and 7 CPUs. You need to install the Minimal version of CentOS7 Linux distribution in order to be able to run OpenStack on top of it. After installation, update your CentOS7 server.

```
yum install epel-release
yum update
```

For accessing remotely to your VIM.

```
sudo yum –y install openssh-server openssh-clients
sudo systemctl status sshd
```

Begin the installation process by executing the following commands to turn off NetworkManager and Firewall on your server and enable normal Networking.

```
sudo systemctl disable firewalld NetworkManager
sudo systemctl enable network
```

Disable SELINUX on your CentOS7 server.

```
sed -i s/^SELINUX=.*$/SELINUX=permissive/ /etc/selinux/config
```

Then if your environment is a non-English locale, change it by adding the following in your /etc/environment. Then reboot your server.

```
LANG=en_US.utf-8
LC_ALL=en_US.utf-8
```

At this point execute the following commands in order to install the required repositories on your server for openstack-stein version.

```
sudo yum update -y
sudo yum install -y centos-release-openstack-stein
sudo yum update -y
sudo yum install -y openstack-packstack
```

Create a configuration file, so-called answer file. You can modify this file and then execute it to install OpenStack all-in-one solution. So, first, execute.

```
packstack --gen-answer-file=answer.txt
```

Apart from your changes in the answer file, do the following modifications in order to map your ethernet interface on the external bridge (br-ex) to have network connectivity to outside of your OpenStack environment

```
--os-neutron-ovs-bridge-mappings=extnet:br-ex 
--os-neutron-ovs-bridge-interfaces=br-ex:<your ethernet interface name> 
--os-neutron-ml2-type-drivers=vxlan,flat
```

Then, execute this command to deploy OpenStack on your server.

```
packstack --answer-file=answer.txt
```

If you get an error regarding Puppet installation, first execute the following command and then redo the previous step.

```
yum downgrade leatherman
```

Create /etc/sysconfig/network-scripts/ifcfg-br-ex and paste the following content in it.

```
DEVICE=br-ex
DEVICETYPE=ovs
TYPE=OVSBridge
BOOTPROTO=static
IPADDR=<your ethernet interface IP Address>
NETMASK=<your network mask>
GATEWAY=<the gateway of your network>
DNS=<the DNS server of your network>
ONBOOT=yes
```

And on your ethernet interface in /etc/sysconfig/network-scripts/ifcfg-<your ethernet interface name>, paste the following content.

```
DEVICE=<your ethernet interface name>
TYPE=OVSPort
DEVICETYPE=ovs
OVS_BRIDGE=br-ex
ONBOOT=yes
```

Finally, execute the following command.

```
service network restart
```

At this point, you should be able to access the OpenStack dashboard by using its credential information located in the keystonerc_admin file.

To use CLI first of all source the keystonerc_admin file and then execute the following commands to download the required images and then import them on the OpenStack dashboard.
For Ubuntu 16.04.

```
wget https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img
openstack image create --file="./xenial-server-cloudimg-amd64-disk1.img" --container-format=bare --disk-format=qcow2 ubuntu1604
```

For Ubuntu 18.04.

```
wget https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-amd64.img
openstack image create --file="./bionic-server-cloudimg-amd64.img" --container-format=bare --disk-format=qcow2 ubuntu1804
```

Integrate your VIM account (OpenStack) to the service orchestrator (OSM). On your OSM machine execute the following.

```
osm vim-create --name <a name for your VIM account> --user <admin or your tenant username> --password <the required password for your tenant account> --auth_url <url of your OpenStack dashboard>:5000/v3/ --tenant <admin or your related tanant name> --account_type openstack --config='{<possible additional configuration on your OpenStack platform>}'
```

# Deploying Network Services

We have created our service orchestrator which is now integrated with one VIM account. For deploying network services, we need to create Virtual Network Function Descriptors (VNFDs) and Network Service Descriptors (NSDs). For creating network slices, some launched instances (services) on the VIM platform are needed to be chained to create one/several network slice(s). In this particular case, OAI EPC/NextEPC and srsLTE RAN are the two VNFs that emulate CN and RAN respectively. Clone the required descriptors from this repository and upload them to the OSM dashboard in order to instantiate network services.

## Creating base images for service instantiation

You should use cloud-based ubuntu images in order to install srsLTE for RAN and OAI EPC/NextEPC for CN.

### OAI EPC installation on ubuntu 

You should install a low latency kernel on Ubuntu 18.04 as a base image for OAI EPC.

```
sudo apt-get install linux-image-lowlatency linux-headers-lowlatency
```

After that, you should install Cassandra which acts as the HSS database for OAI EPC.

```
echo "deb http://www.apache.org/dist/cassandra/debian 21x main" | $SUDO  tee -a /etc/apt/sources.list.d/cassandra.sources.list
curl https://downloads.apache.org/cassandra/KEYS | $SUDO  apt-key add –
$SUDO $INSTALLER install $OPTION curl openjdk-8-jre

```

Reboot the instance in order to make the changes. Then, you should clone OAI from its main repository.

```
git clone https://github.com/OPENAIRINTERFACE/openair-cn.git
cd openair-cn/scripts
git checkout develop
cd ..
```
```
git clone https://github.com/OPENAIRINTERFACE/openair-cn-cups.git
cd openair-cn-cups/                  
git checkout develop
```
#### OAI EPC - HSS 
First, go to the following directory and execute these commands one after another.

```
cd openair-cn/scripts
./build_cassandra --check-installed-software --force
sudo service cassandra stop
sudo update-alternatives --config java
sudo service cassandra start
sudo service cassandra stop
sudo rm -rf /var/lib/cassandra/data/system/*
sudo rm -rf /var/lib/cassandra/commitlog/*
sudo rm -rf /var/lib/cassandra/data/system_traces/*
sudo rm -rf /var/lib/cassandra/saved_caches/*
sudo service cassandra start
./build_hss_rel14 --check-installed-software --force
./build_hss_rel14 --clean
Cassandra_Server_IP='127.0.0.1'
MY_REALM='srslte.com'
cqlsh --file ../src/hss_rel14/db/oai_db.cql $Cassandra_Server_IP
./data_provisioning_users --apn default.srslte.com --apn2 internet --key 6FD60656E2B7F86FBEE9A31518AC18BE --imsi-first 901700000011201 --msisdn-first 001010000011201 --mme-identity mme.$MY_REALM --no-of-users 20 --realm $MY_REALM --truncate True  --verbose True --cassandra-cluster $Cassandra_Server_IP

./data_provisioning_mme --id 3 --mme-identity mme.$MY_REALM --realm $MY_REALM --ue-reachability 1 --truncate True  --verbose True -C $Cassandra_Server_IP

openssl rand -out $HOME/.rnd 128
PREFIX='/usr/local/etc/oai'
sudo mkdir -m 0777 -p $PREFIX
sudo mkdir -m 0777 -p $PREFIX/freeDiameter
sudo mkdir -m 0777 -p $PREFIX/logs
sudo mkdir -m 0777 -p logs
sudo chmod 777 $PREFIX
sudo chmod 777 $PREFIX/freeDiameter
sudo chmod 777 $PREFIX/logs
sudo chmod 777 logs
sudo cp ../etc/acl.conf ../etc/hss_rel14_fd.conf $PREFIX/freeDiameter
sudo cp ../etc/hss_rel14.conf ../etc/hss_rel14.json $PREFIX
sudo cp ../etc/oss.json $PREFIX
declare -A HSS_CONF
HSS_CONF[@PREFIX@]=$PREFIX
HSS_CONF[@REALM@]=$MY_REALM
HSS_CONF[@HSS_FQDN@]="hss.${HSS_CONF[@REALM@]}"
HSS_CONF[@cassandra_Server_IP@]=$Cassandra_Server_IP
HSS_CONF[@OP_KEY@]='AF8C8C9B229BFADC722A74A3FBF3A490'
HSS_CONF[@ROAMING_ALLOWED@]='true'
for K in "${!HSS_CONF[@]}"; do  egrep -lRZ "$K" $PREFIX | xargs -0 -l sed -i -e "s|$K|${HSS_CONF[$K]}|g"; done
../src/hss_rel14/bin/make_certs.sh hss ${HSS_CONF[@REALM@]} $PREFIX
sudo sed -i -e 's/#ListenOn/ListenOn/g' $PREFIX/freeDiameter/hss_rel14_fd.conf
oai_hss -j $PREFIX/hss_rel14.json –onlyloadkey
```

#### OAI EPC - MME

Remain in the same directory and follow up these commands to install MME. Notice to change MCC and MNC according to your SIM Card information or program the SIM Card with your favorite values.

```
./build_mme --check-installed-software --force
./build_mme --clean
virsh net-list --all
openssl rand -out $HOME/.rnd 128
INSTANCE=1
PREFIX='/usr/local/etc/oai'
cp ../etc/mme_fd.sprint.conf  $PREFIX/freeDiameter/mme_fd.conf
cp ../etc/mme.conf  $PREFIX
declare -A MME_CONF
MME_CONF[@MME_S6A_IP_ADDR@]="127.0.0.11"
MME_CONF[@INSTANCE@]=$INSTANCE
MME_CONF[@PREFIX@]=$PREFIX
MME_CONF[@REALM@]='srslte.com'
MME_CONF[@PID_DIRECTORY@]='/var/run'
MME_CONF[@MME_FQDN@]="mme.${MME_CONF[@REALM@]}"
MME_CONF[@HSS_HOSTNAME@]='hss'
MME_CONF[@HSS_FQDN@]="${MME_CONF[@HSS_HOSTNAME@]}.${MME_CONF[@REALM@]}"
MME_CONF[@HSS_IP_ADDR@]='127.0.0.1'
MME_CONF[@MCC@]='<your MCC of your SIMCard>'
MME_CONF[@MNC@]='<your MNC of your SIMCard>'
MME_CONF[@MME_GID@]='4'
MME_CONF[@MME_CODE@]='1'
MME_CONF[@TAC_0@]='600'
MME_CONF[@TAC_1@]='601'
MME_CONF[@TAC_2@]='602'
MME_CONF[@MME_INTERFACE_NAME_FOR_S1_MME@]='ens3:m1c'
MME_CONF[@MME_IPV4_ADDRESS_FOR_S1_MME@]='192.168.247.102/24'
MME_CONF[@MME_INTERFACE_NAME_FOR_S11@]='ens3:m11'
MME_CONF[@MME_IPV4_ADDRESS_FOR_S11@]='172.16.1.102/24'
MME_CONF[@MME_INTERFACE_NAME_FOR_S10@]='ens3:m10'
MME_CONF[@MME_IPV4_ADDRESS_FOR_S10@]='192.168.10.110/24'
MME_CONF[@OUTPUT@]='CONSOLE'
MME_CONF[@SGW_IPV4_ADDRESS_FOR_S11_TEST_0@]='172.16.1.104/24'
MME_CONF[@SGW_IPV4_ADDRESS_FOR_S11_0@]='172.16.1.104/24'
MME_CONF[@PEER_MME_IPV4_ADDRESS_FOR_S10_0@]='0.0.0.0/24'
MME_CONF[@PEER_MME_IPV4_ADDRESS_FOR_S10_1@]='0.0.0.0/24'
TAC_SGW_TEST='7'
tmph=`echo "$TAC_SGW_TEST / 256" | bc`
tmpl=`echo "$TAC_SGW_TEST % 256" | bc`
MME_CONF[@TAC-LB_SGW_TEST_0@]=`printf "%02x\n" $tmpl`
MME_CONF[@TAC-HB_SGW_TEST_0@]=`printf "%02x\n" $tmph`
MME_CONF[@MCC_SGW_0@]=${MME_CONF[@MCC@]}
MME_CONF[@MNC3_SGW_0@]=`printf "%03d\n" $(echo ${MME_CONF[@MNC@]} | sed 's/^0*//')`
TAC_SGW_0='600'
tmph=`echo "$TAC_SGW_0 / 256" | bc`
tmpl=`echo "$TAC_SGW_0 % 256" | bc`
MME_CONF[@TAC-LB_SGW_0@]=`printf "%02x\n" $tmpl`
MME_CONF[@TAC-HB_SGW_0@]=`printf "%02x\n" $tmph`
MME_CONF[@MCC_MME_0@]=${MME_CONF[@MCC@]}
MME_CONF[@MNC3_MME_0@]=`printf "%03d\n" $(echo ${MME_CONF[@MNC@]} | sed 's/^0*//')`
TAC_MME_0='601'
tmph=`echo "$TAC_MME_0 / 256" | bc`
tmpl=`echo "$TAC_MME_0 % 256" | bc`
MME_CONF[@TAC-LB_MME_0@]=`printf "%02x\n" $tmpl`
MME_CONF[@TAC-HB_MME_0@]=`printf "%02x\n" $tmph`
MME_CONF[@MCC_MME_1@]=${MME_CONF[@MCC@]}
MME_CONF[@MNC3_MME_1@]=`printf "%03d\n" $(echo ${MME_CONF[@MNC@]} | sed 's/^0*//')`
TAC_MME_1='602'
tmph=`echo "$TAC_MME_1 / 256" | bc`
tmpl=`echo "$TAC_MME_1 % 256" | bc`
MME_CONF[@TAC-LB_MME_1@]=`printf "%02x\n" $tmpl`
MME_CONF[@TAC-HB_MME_1@]=`printf "%02x\n" $tmph`

for K in "${!MME_CONF[@]}"; do    egrep -lRZ "$K" $PREFIX | xargs -0 -l sed -i -e "s|$K|${MME_CONF[$K]}|g";   ret=$?;[[ ret -ne 0 ]] && echo "Tried to replace $K with ${MME_CONF[$K]}"; done

sudo ./check_mme_s6a_certificate $PREFIX/freeDiameter mme.${MME_CONF[@REALM@]}

```

#### OAI EPC - SPGWC and SPGWU

Then you should change the directory in order to install the control plane and data plane of SPGW.

```
cd openair-cn-cupscd/build/scripts
./build_spgwc -I -f
./build_spgwc -c -V -b Debug -j
INSTANCE=1
PREFIX='/usr/local/etc/oai'
sudo mkdir -m 0777 -p $PREFIX
sudo chmod 777 $PREFIX
cp ../../etc/spgw_c.conf  $PREFIX
declare -A SPGWC_CONF
SPGWC_CONF[@INSTANCE@]=$INSTANCE
SPGWC_CONF[@PID_DIRECTORY@]='/var/run'
SPGWC_CONF[@SGW_INTERFACE_NAME_FOR_S11@]='ens3:s11'
SPGWC_CONF[@SGW_INTERFACE_NAME_FOR_S5_S8_CP@]='ens3:s5c'
SPGWC_CONF[@PGW_INTERFACE_NAME_FOR_S5_S8_CP@]='ens3:p5c'
SPGWC_CONF[@PGW_INTERFACE_NAME_FOR_SX@]='ens3:sxc'
SPGWC_CONF[@DEFAULT_DNS_IPV4_ADDRESS@]='129.241.0.200'
SPGWC_CONF[@DEFAULT_DNS_SEC_IPV4_ADDRESS@]='129.241.0.201'
for K in "${!SPGWC_CONF[@]}"; do egrep -lZ "$K" $PREFIX/spgw_c.conf | xargs -0 -l sed -i -e "s|$K|${SPGWC_CONF[$K]}|g"; ret=$?;[[ ret -ne 0 ]] && echo "Tried to replace $K with ${SPGWC_CONF[$K]}"; done

./build_spgwu -I -f
./build_spgwu -c -V -b Debug -j
INSTANCE=1
PREFIX='/usr/local/etc/oai'
sudo mkdir -m 0777 -p $PREFIX
sudo chmod 777 $PREFIX
cp ../../etc/spgw_u.conf  $PREFIX
declare -A SPGWU_CONF
SPGWU_CONF[@INSTANCE@]=$INSTANCE
SPGWU_CONF[@PID_DIRECTORY@]='/var/run'
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_S1U_S12_S4_UP@]='ens3:s1u'
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_SX@]='ens3:sxu'
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_SGI@]='ens3'
for K in "${!SPGWU_CONF[@]}"; do  egrep -lZ "$K" $PREFIX/spgw_u.conf | xargs -0 -l sed -i -e "s|$K|${SPGWU_CONF[$K]}|g"; ret=$?;[[ ret -ne 0 ]] && echo "Tried to replace $K with ${SPGWU_CONF[$K]}"; done
```

Then you should configure all the required interfaces with the following commands according to your ethernet interface name and IP address.
```
sudo ifconfig <ethernet interface name in our case: ens3> <ethernet IP address in our case: 192.168.166.146> up

sudo ifconfig ens3 192.168.166.146 up
sudo ifconfig ens3:m1c 192.168.247.102 up
sudo ifconfig ens3:s1u 192.168.248.159 up
sudo ifconfig ens3:m11 172.16.1.102 up
sudo ifconfig ens3:m10 192.168.10.110 up
sudo ifconfig ens3:sxu 172.55.55.102 up
sudo ifconfig ens3:sxc 172.55.55.101 up
sudo ifconfig ens3:s5c 172.58.58.102 up
sudo ifconfig ens3:p5c 172.58.58.101 up
sudo ifconfig ens3:s11 172.16.1.104 up 
```

These values should be considered while creating and configuring descriptors.

### SRS LTE installation on ubuntu 

You should install a low latency kernel on Ubuntu 18.04 as a base image for srsLTE eNB.

```
sudo apt-get install linux-image-lowlatency linux-headers-lowlatency
```

For the case of srsLTE, we installed the required package from 5G-EmPOWER repository which is a customized version of srsLTE that is compatible with EmPOWER-Agent. EmPOWER-Agent acts as a mediator between the eNB and 5G-EmPOWER controller that is an SDN controller for the RAN domain. First of all, you should install some dependencies in your instance.

```
sudo apt-get install cmake git libfftw3-dev libmbedtls-dev libboost-program-options-dev libconfig++-dev libsctp-dev libuhd-dev
```

Then, clone EmPOWER repository for srsLTE eNB and then execute the following commands one after another.

```
sudo apt-get update
git clone https://github.com/5g-empower/srsLTE-20.04.git
cd srsLTE-20.04
mkdir build 
cd build 
cmake ../ 
make
make test
sudo make install
srslte_install_configs.sh user
cd ~/srsLTE-20.04
cp srsenb/drb.conf.example build/srsenb/src/drb.conf
cp srsenb/enb.conf.example build/srsenb/src/enb.conf
cp srsenb/rr.conf.example build/srsenb/src/rr.conf
cp srsenb/sib.conf.example build/srsenb/src/sib.conf
```

#### USRP installation

At this point since the Base Band Unit (BBU) has been installed (srsLTE eNB), we need to connect it to a possible Remote Radio Unit (RRU). In our case, we use a USRP b210. The following shows how to configure the host machine (Ubuntu 18.04) in order to connect to the USRP b210. Do not connect USRP to your host machine.

```
sudo apt-get update
sudo apt-get -y install git swig cmake doxygen build-essential libboost-all-dev libtool libusb-1.0-0 libusb-1.0-0-dev libudev-dev libncurses5-dev libfftw3-bin libfftw3-dev libfftw3-doc libcppunit-1.14-0 libcppunit-dev libcppunit-doc ncurses-bin cpufrequtils python-numpy python-numpy-doc python-numpy-dbg python-scipy python-docutils qt4-bin-dbg qt4-default qt4-doc libqt4-dev libqt4-dev-bin python-qt4 python-qt4-dbg python-qt4-dev python-qt4-doc python-qt4-doc libqwt6abi1 libfftw3-bin libfftw3-dev libfftw3-doc ncurses-bin libncurses5 libncurses5-dev libncurses5-dbg libfontconfig1-dev libxrender-dev libpulse-dev swig g++ automake autoconf libtool python-dev libfftw3-dev libcppunit-dev libboost-all-dev libusb-dev libusb-1.0-0-dev fort77 libsdl1.2-dev python-wxgtk3.0 git libqt4-dev python-numpy ccache python-opengl libgsl-dev python-cheetah python-mako python-lxml doxygen qt4-default qt4-dev-tools libusb-1.0-0-dev libqwtplot3d-qt5-dev pyqt4-dev-tools python-qwt5-qt4 cmake git wget libxi-dev gtk2-engines-pixbuf r-base-dev python-tk liborc-0.4-0 liborc-0.4-dev libasound2-dev python-gtk2 libzmq3-dev libzmq5 python-requests python-sphinx libcomedi-dev python-zmq libqwt-dev libqwt6abi1 python-six libgps-dev libgps23 gpsd gpsd-clients python-gps python-setuptools

cd $HOME
mkdir workarea
cd workarea
git clone https://github.com/EttusResearch/uhd
cd uhd
 ```
 
According to the UHD version of USRP b210, you should check out the desired UHD version. Then install the specific version. Finally, update the library cache.
 
 ```
git tag -l
git checkout <UHD version>
cd host
mkdir build
cd build
cmake ../
make
make test
sudo make install
sudo ldconfig
 ```
 
You need to set the 'UHD_IMAGES_DIR' environment variable appropriately in .bashrc as the following.

 ```
 export UHD_IMAGES_DIR=/usr/local/share/uhd/images
 ```
 
Finally, you need to download the UHD FPGA Images.

```
sudo uhd_images_downloader
```
 
At this point, connect USRP to the host machine and execute the following commands. You need to configure USB port of USRP as well (only for USRPs which has USB port instead of ethernet port).

```
sudo uhd_images_downloader
cd $HOME/workarea/uhd/host/utils
sudo cp uhd-usrp.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Now you can verify the connectivity by these commands.

```
uhd_find_devices
uhd_usrp_probe
```




















































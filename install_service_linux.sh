#!/bin/bash

pip3 install -r requirement.txt

case `uname` in
  Linux )
     LINUX=1
     which apk && {
        echo "Alpine"
        mkdir -p /usr/local/bunny-cdn-failover
        \cp -f config.yml /usr/local/bunny-cdn-failover
        \cp -f main.py /usr/local/bunny-cdn-failover

        cat > /etc/local.d/bunny-cdn-failover.start << EOF
cd /usr/local/bunny-cdn-failover/
nohup /usr/bin/python3 /usr/local/bunny-cdn-failover/main.py &

EOF

        chmod +x /etc/local.d/bunny-cdn-failover.start
        rc-update add local
        rc-service local start
        }
     (which yum || which apt-get) && { 
        echo "CentOS or Debian"
        mkdir -p /usr/local/bunny-cdn-failover
        \cp -f main.py /usr/local/bunny-cdn-failover
        \cp -f config.yml /usr/local/bunny-cdn-failover

        cat > /lib/systemd/system/bunny-cdn-failover.service << EOF
[Unit]
Description=server bunny-cdn-failover
After=network.target

[Service]
User=root
ExecStart=/usr/bin/python3 /usr/local/bunny-cdn-failover/main.py
WorkingDirectory=/usr/local/bunny-cdn-failover/
Restart=always

[Install]
WantedBy=multi-user.target

EOF
        systemctl daemon-reload
        systemctl start bunny-cdn-failover
        systemctl enable bunny-cdn-failover
        }
     ;;
  Darwin )
     DARWIN=1
     ;;
  * )
     # Handle AmigaOS, CPM, and modified cable modems.
     ;;
esac


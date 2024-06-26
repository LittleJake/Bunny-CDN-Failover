from scapy.all import *
import yaml
import requests
import logging
import time
from urllib.parse import urlparse
import socket
import threading

# load yaml
extDataDir = os.getcwd()
with open(os.path.join(extDataDir, 'config.yml'))as f:
	CONFIG = yaml.load(f,Loader=yaml.SafeLoader)

# configure scapy for supporting loopback interface
conf.L3socket=L3RawSocket

# setting global timeout
socket.setdefaulttimeout(CONFIG['Timeout'])

# setting logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

UPSTREAM = {}

def icmp_check(ip):
    ans, _  = sr( IP(dst=ip)/ICMP() , timeout=CONFIG['Timeout'], verbose=False)
    if len(ans) != 0:
        return True

    return False

def tcp_check(ip, port):
#     ans, _ = sr( IP(dst=ip)/TCP(dport=port, flags="S") , timeout=CONFIG['Timeout'], verbose=False)
#     if len(ans) != 0:
#         return True

#     return False

    try:
        family, type, _, _, sockaddr = socket.getaddrinfo(ip, port, proto=socket.IPPROTO_TCP)[0]
        s = socket.socket(family, type)
        s.connect(sockaddr)
        s.close()
        return True
    except:
        return False


def url_check(url):
    o = urlparse(url)
    if o.scheme == 'http': port = 80
    elif o.scheme == 'https': port = 443
    else: port = o.port

    logging.debug("Sending tcp pkt to %s:%d" % (o.hostname, port))
    
    try:
        resp = requests.get(url=url, timeout=CONFIG['Timeout'], verify=False)
        return resp.ok
    except:
        return tcp_check(o.hostname, port)
            


def fetch_zone(zone_id):
    headers = {
        "accept": "application/json",
        "AccessKey": CONFIG['AccessKey']
    }
    resp = requests.get(url="https://api.bunny.net/pullzone/%s" % zone_id, headers=headers)
    return resp.json()




def update_zone_origin(zone_id, origin_url, origin_host):
    headers = {
        "accept": "application/json",
        "AccessKey": CONFIG['AccessKey']
    }
    resp = requests.post(url="https://api.bunny.net/pullzone/%s" % zone_id, headers=headers, json={'OriginUrl': origin_url, 'OriginHostHeader': origin_host})
    return resp.ok

def init_upstreams():
    global UPSTREAM
    for zone_id in CONFIG["Zone"].keys():
        logging.debug("Initial zone %d." % zone_id)
        UPSTREAM.setdefault(zone_id, fetch_zone(zone_id))
    pass


def get_available_upstream():
    for zone_id in CONFIG["Zone"].keys():
        print(zone_id)
        UPSTREAM.setdefault(zone_id, fetch_zone(zone_id))
    pass

def health_check(zone_id):
    global UPSTREAM
    old_origin_url = UPSTREAM[zone_id]["OriginUrl"]
    result = url_check(old_origin_url)
    logging.info("Zone %d(%s) is ok? %s" % (zone_id, old_origin_url, result))
    # check_type = CONFIG[zone_id]
    if result: return
    logging.debug("Checking zone %d for new origin" % zone_id)

    flag = False
    for url, v in CONFIG["Zone"][zone_id]["OriginUrl"].items():
        if url_check(url):
            update_zone_origin(zone_id, url, v["host_header"])
            UPSTREAM[zone_id] = fetch_zone(zone_id)
            flag = True
            logging.info("Update zone %d upstream: %s -> %s" % (zone_id, old_origin_url, url))
            break
    
    if not flag: logging.debug("No more upstream for zone %d available." % zone_id)


def main():
    # fetch all zone
    init_upstreams()
    while True:
        try:
            logging.info("Checking origin.")
            for zone_id in UPSTREAM.keys():
                health_check(zone_id)

        except Exception as e:
            logging.error(e)
            logging.error("ERROR OCCUR.")
        time.sleep(CONFIG['Interval'])
		
if __name__ == '__main__':
	main()


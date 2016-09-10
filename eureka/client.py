import random
from urllib2 import URLError
from urlparse import urljoin
from eureka import requests
import ec2metadata
import logging
import dns.resolver
from eureka.requests import EurekaHTTPException
import sys
import time
from time import sleep
import json
import threading

logger = logging.getLogger('eureka.client')


class EurekaClientException(Exception):
    pass


class EurekaRegistrationFailedException(EurekaClientException):
    pass


class EurekaUpdateFailedException(EurekaClientException):
    pass


class EurekaHeartbeatFailedException(EurekaClientException):
    pass


class EurekaGetFailedException(EurekaClientException):
    pass

class EurekaLogOutFailedException(EurekaClientException):
    pass

class EurekaClient(object):
    def __init__(self, app_name, eureka_urls=None, use_dns=True, region=None,
                 context="eureka/v2",eureka_port=None, host_name=None, data_center="MyOwn",
                 ip_address=None, vip_address=None, secure_vip_address=None,
                 port=None, secure_port=None, prefer_same_zone=True,
                 homePageUrl=None, secure_health_check_url="",
                 health_check_urls=None, statusPageUrls=None, metadata=None,heartbeatInterval=None,heartbeatDuration=None):
        super(EurekaClient, self).__init__()
        self.app_name = app_name
        self.eureka_urls = eureka_urls
        self.data_center = data_center
        if not host_name and data_center == "Amazon":
            self.host_name = ec2metadata.get("public-hostname")
        else:
            self.host_name = host_name
        # Virtual host name by which the clients identifies this service
        self.ip_address = ip_address
        self.vip_address = vip_address
        self.secure_vip_address = secure_vip_address
        self.port = port
        self.secure_port = secure_port
        self.use_dns = use_dns
        # Region where eureka is deployed - For AWS specify one of the AWS regions, for other datacenters specify a
        # arbitrary string indicating the region.
        self.heartbeatInterval = heartbeatInterval
        # Prefer a eureka server in same zone or not
        self.heartbeatDuration = heartbeatDuration
        #if eureka runs on a port that is not 80, this will go into the urls to eureka
        self.eureka_port = eureka_port
        # Relative URL to eureka
        self.context = context
        self.healthCheckUrls = health_check_urls
        self.secure_health_check_url = secure_health_check_url
        self.homePageUrl = homePageUrl
        self.statusPageUrls = statusPageUrls
        self.metadata = metadata

    def register(self, initial_status="UP"):
        data_center_info = {
            'name': self.data_center,
            '@class': 'com.netflix.appinfo.DataCenterInfo'
        }
        if self.data_center == "Amazon":
            data_center_info['metadata'] = {
                'ami-launch-index': ec2metadata.get('ami-launch-index'),
                'local-hostname': ec2metadata.get('local-hostname'),
                'availability-zone': ec2metadata.get('availability-zone'),
                'instance-id': ec2metadata.get('instance-id'),
                'public-ipv4': ec2metadata.get('public-ipv4'),
                'public-hostname': ec2metadata.get('public-hostname'),
                'ami-manifest-path': ec2metadata.get('ami-manifest-path'),
                'local-ipv4': ec2metadata.get('local-ipv4'),
                'ami-id': ec2metadata.get('ami-id'),
                'instance-type': ec2metadata.get('instance-type'),
            }
        instance_data = {
            "instance":{
                "hostName": self.host_name,
                "instanceId":self.host_name+":"+self.app_name+":"+str(self.port),
                "app": self.app_name,
                "ipAddr": self.ip_address,
                "vipAddress": self.vip_address or "",
                "secureVipAddress": self.secure_vip_address or "",
                "status": initial_status,
                "dataCenterInfo": data_center_info,
                #"healthCheckUrl": self.healthCheckUrl,
                "secureHealthCheckUrl": self.secure_health_check_url,
                #"statusPageUrl": self.statusPageUrl,
                "homePageUrl": self.homePageUrl,
                "metadata": {"@class":"java.util.Collections$EmptyMap"},
                "leaseInfo":{
                    "durationInSecs":self.heartbeatDuration,
                    "renewalIntervalInSecs":self.heartbeatInterval,
                    "evictionTimestamp":"",
                    "lastRenewalTimestamp":"",
                    "serviceUpTimestamp":str(int(time.time())),
                    "registrationTimestamp":str(int(time.time()))
                }
            }
        }
        if self.port:
            instance_data["instance"]["port"] = {
                "$": self.port,
                "@enabled": True
            }
        if self.secure_port:
            instance_data["instance"]["securePort"] = {
                "$": self.secure_port,
                "@enabled": True
            }

        success = False
        for i in xrange(len(self.eureka_urls)):
            try:
                instance_data["instance"]["healthCheckUrl"] =self.healthCheckUrls[i] 
                instance_data["instance"]["statusPageUrl"] = self.statusPageUrls[i]
                r = requests.post(urljoin(self.eureka_urls[i], "apps/%s" % self.app_name), json.dumps(instance_data),
                                            headers={'Content-Type': 'application/json'})
                r[0].raise_for_status()
                success = True
                break
            except (EurekaHTTPException, URLError):
                pass
        if not success:
            raise EurekaRegistrationFailedException("Did not receive correct reply from any instances"), None, sys.exc_info()[2]

    def get_instances(self):
        return self.host_name+':'+self.app_name+':'+str(self.port)

    def update_status(self, new_status):
        instance_id = get_instances(self)
        if self.data_center == "Amazon":
            instance_id = ec2metadata.get('instance-id')
        success = False
        for eureka_url in self.eureka_urls:
            try:
                r = requests.put(urljoin(eureka_url, "apps/%s/%s/status?value=%s" % (
                    self.app_name,
                    instance_id,
                    new_status
                )))
                r.raise_for_status()
                success = True
                break
            except (EurekaHTTPException, URLError) as e:
                pass
        if not success:
            raise EurekaUpdateFailedException("Did not receive correct reply from any instances"), None, sys.exc_info()[2]

    def heartbeat(self,instance_id):
        while True:
            print 'run'
            if self.data_center == "Amazon":
                instance_id = ec2metadata.get('instance-id')
            success = False
            for i in xrange(len(self.eureka_urls)):
                try:
                    # instance_data["instance"]["healthCheckUrl"] =self.healthCheckUrls[i] 
                    # instance_data["instance"]["statusPageUrl"] = self.statusPageUrls[i]
                    r = requests.put(urljoin(self.eureka_urls[i], "apps/%s/%s" % (self.app_name, instance_id)))
                    r[0].raise_for_status()
                    success = True
                    break
                except (EurekaHTTPException, URLError) as e:
                    pass
            if not success: 
                raise EurekaHeartbeatFailedException("Did not receive correct reply from any instances"), None, sys.exc_info()[2]
            time.sleep(int(self.heartbeatInterval))

    def de_register(self):
        instance_id = get_instances()
        for i in xrange(len(self.eureka_urls)):
            try:
                r = requests.delete(urljoin(self.eureka_urls[i], "apps/%s/%s" % (self.app_name, instance_id)))
                r[0].raise_for_status()
                success = True
            except (EurekaHTTPException, URLError) as e:
                pass
        if not success: 
            raise EurekaLogOutFailedException("Did not de-register correctly from instances"), None, sys.exc_info()[2]

    def get_apps(self):
        return self._get_from_any_instance("apps")

    def get_app(self, app_id):
        return self._get_from_any_instance("apps/%s" % app_id)

    def get_vip(self, vip_address):
        return self._get_from_any_instance("vips/%s" % vip_address)

    def get_svip(self, vip_address):
        return self._get_from_any_instance("svips/%s" % vip_address)

    def get_instance(self, instance_id):
        return self._get_from_any_instance("instances/%s" % instance_id)

    def get_app_instance(self, app_id, instance_id):
        return self._get_from_any_instance("apps/%s/%s" % (app_id, instance_id))


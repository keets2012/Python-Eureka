from eureka import requests
from urllib2 import URLError
from urlparse import urljoin
import json
from eureka import client
from eureka.requests import EurekaHTTPException
from eureka.client import EurekaClientException
from eureka.client import EurekaGetFailedException
import dns.resolver


class EurekaConnect:
    def __init__(self,config_url):
    	self.config_url = config_url

    #pull config from remote server
    def get_remote_config(self):
        try:
            url = urljoin(self.config_url, "eurekaserver/expeureka01")
            r, res = requests.get(url, headers={'Accept': 'application/json'})
            r.raise_for_status()
            configs = json.loads(res)
            eureka_urls = []
            ports = []
            for item in configs['propertySources']:
                eureka_urls.append(item['source']['eureka.client.serviceUrl.defaultZone'])
                ports.append(item['source']['server.port'])
            return eureka_urls,ports
        except (EurekaHTTPException, URLError):
            raise EurekaGetFailedException("Failed to GET from all configs" ), None, sys.exc_info()[2]

python-eureka version - 2.1M
=============
Python client for Netflix Eureka https://github.com/Netflix/eureka/

I upgrade based on https://github.com/KristianOellegaard/python-eureka.

As KristianOellegaard's Eureka version is too old and not compatible with newer version.


The goal of this project is to provide an easy-to-use client interface to Eureka,
a middle-tier load balancer open sourced and used by Netflix.

It's fairly straight forward to use once you hve setup Eureka itself. Consider the following script (to be run on EC2):

```python

from eureka.client import EurekaClient
import logging

logging.basicConfig()


ec = EurekaClient("MyApplication",
                  eureka_domain_name="test.yourdomain.net",
                  region="eu-west-1",
                  vip_address="http://app.yourdomain.net/",
                  port=80,
                  secure_vip_address="https://app.yourdomain.net/",
                  secure_port=443
)
print ec.get_zones_from_dns()
print ec.get_eureka_urls()
print ec.register()
print ec.update_status("UP")  # Or ec.register("UP")
print ec.heartbeat()

```

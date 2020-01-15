#!/usr/bin/env python3
import boto3
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import os
import sys

# AWS
session = boto3.session.Session(region_name='eu-west-1')
ec2 = session.resource('ec2')
client = session.client('ec2')

PUSHGATEWAY_SERVICE_HOST = os.getenv('PUSHGATEWAY_SERVICE_HOST')
PUSHGATEWAY_SERVICE_PORT_HTTP = os.getenv('PUSHGATEWAY_SERVICE_PORT_HTTP')

if not PUSHGATEWAY_SERVICE_HOST or not PUSHGATEWAY_SERVICE_PORT_HTTP:
    sys.exit('Error: pushgateway not found')

# prometheus stuff
registry = CollectorRegistry()
g = Gauge(
    'available_ip',
    'available ip addresses per subnet',
    ['vpc_id', 'subnet_id'],
    registry=registry)

# get VPCs and subnets
for vpc in ec2.vpcs.all():
    for subnet in vpc.subnets.all():
        availableIps = client.describe_subnets(
            SubnetIds=[
                subnet.id
            ]
        )['Subnets'][0]['AvailableIpAddressCount']

        # pushgateway
        g.labels(vpc_id=vpc.id, subnet_id=subnet.id).set(availableIps)

# push all the things
push_to_gateway(f"{PUSHGATEWAY_SERVICE_HOST}:{PUSHGATEWAY_SERVICE_PORT_HTTP}",
                job='ipaddresses', registry=registry)

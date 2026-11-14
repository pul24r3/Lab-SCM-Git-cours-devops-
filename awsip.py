import urllib.request
import json
import ipaddress
import sys

def download_aws_ip_set():
  """Downloads the AWS IP range JSON file and returns it as a dictionary."""

  # URL of the AWS IP range JSON file
  aws_ip_range_url = 'https://ip-ranges.amazonaws.com/ip-ranges.json'

  # Download the JSON file
  with urllib.request.urlopen(aws_ip_range_url) as url:
    aws_ip_range_data = json.load(url)

  return aws_ip_range_data['prefixes']

# Find ip given IP belongs to any AWS Service
def find_aws_ip(aws_ip_range_data, ip_to_find):
  """Finds the AWS IP ranges containing the given IP address,
  with the first IP, last IP and number of addresses of each range."""
  ip = ipaddress.ip_address(ip_to_find)  # calculé une seule fois
  results = []

  for prefix in aws_ip_range_data:
    network = ipaddress.ip_network(prefix['ip_prefix'])
    if ip in network:
      results.append({
        **prefix,                                    # champs d'origine conservés
        'first_ip': str(network.network_address),    # première IP de la plage
        'last_ip': str(network.broadcast_address),   # dernière IP de la plage
        'num_addresses': network.num_addresses       # nombre d'adresses
      })

  return results

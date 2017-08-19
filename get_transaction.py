import json
import requests

def get_transaction(tx_hash):
  url = 'http://localhost:8545'
  headers = {'content-type': 'application/json'}
  request = {
      'jsonrpc': '2.0', 'id': 1,
      'method': 'eth_getTransactionByHash',
      'params': [tx_hash]
  }
  return requests.post(
          url, data=json.dumps(request), headers=headers).json()

print get_transaction('0x314e0246cfc55bc0882cbf165145c168834e99924e3ff7619ebd8290e713386d')

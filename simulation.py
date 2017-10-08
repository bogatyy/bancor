"""Simulate Bancor front-running ROI."""

from __future__ import print_function

from one_frontrun import send_request, parse_tx_data

BANCOR_PURCHASE = '0x77a77eca75445841875ebb67a33d0a97dc34d924'
BANCOR_CHANGER = '0xca83bd8c4c7b1c0409b25fbd7e70b1ef57629ff4'
CHANGE_METHOD = '0x5e5144eb'
BANCOR_TOKEN = '0x1f573d6fb3f13d689ff844b4ce37794d79a7ff1c'
ETH_ERC20_TOKEN = '0xd76b5c2a23ef78368d8e34288b5b65d616b746ae'

TOTAL_RESERVE = 80e3  # Total Bancor reserve was 80K ETH at highest point.
ETH_PRICE = 300.0
BLOCK_JUL01 = 3960000
BLOCK_AUG01 = 4105000
BLOCK_SEP01 = 4226000
WEI_TO_ETH = 1e-18
BNT_TO_ETH = 1e-2


def get_tx_value_in_eth(tx):
  if tx[u'to'] == BANCOR_PURCHASE:
    return int(tx[u'value'], 16) * WEI_TO_ETH
  elif tx[u'to'] == BANCOR_CHANGER:
    try:
      method, from_token, to_token, amount, min_return = parse_tx_data(
          tx[u'input'])
    except Exception:
      return 0.0
    if method != int(CHANGE_METHOD, 16):
      return 0.0
    if set([from_token, to_token]) != set(
        [int(BANCOR_TOKEN, 16), int(ETH_ERC20_TOKEN, 16)]):
      print('Wrong from/to addresses', tx[u'hash'])
      return 0.0
    receipt = send_request({
        'method': 'eth_getTransactionReceipt',
        'params': [tx[u'hash']]
    })
    if not receipt[u'logs']:
      # Invalid transaction
      return 0.0
    if from_token == int(ETH_ERC20_TOKEN, 16):
      return amount * WEI_TO_ETH
    else:
      return amount * WEI_TO_ETH * BNT_TO_ETH
  else:
    return 0.0


def run_simulation():
  one_percent = (BLOCK_SEP01 - BLOCK_JUL01) // 100
  large_transactions_jul = []
  large_transactions_aug = []
  for block_number in xrange(BLOCK_JUL01, BLOCK_SEP01):
    if (block_number - BLOCK_JUL01) % one_percent == 0:
      print('{0}% done'.format((block_number - BLOCK_JUL01) // one_percent))
    block = send_request({
        'method': 'eth_getBlockByNumber',
        'params': [hex(block_number), True]
    })
    for tx in block[u'transactions']:
      value = get_tx_value_in_eth(tx)
      if value > 99.0:
        print('Found a large transaction', value, tx[u'hash'])
        if block_number < BLOCK_AUG01:
          large_transactions_jul.append(value)
        else:
          large_transactions_aug.append(value)

  print('All large TXs in July:  ', large_transactions_jul)
  print('All large TXs in August:', large_transactions_aug)
  get_roi = lambda tx_values: 100.0 * sum(tx_values) / TOTAL_RESERVE
  print('ROI front-running all transaction >= 100 ETH: July {0}% August {1}%'.
        format(
            get_roi(large_transactions_jul), get_roi(large_transactions_aug)))
  print('With a principal of 100 ETH, that would make you {0}$'.format(
      get_roi(large_transactions_jul + large_transactions_aug) * ETH_PRICE))


if __name__ == '__main__':
  run_simulation()


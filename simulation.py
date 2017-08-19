"""Simulation"""

from one_frontrun import log, send_request, parse_tx_data
from one_frontrun import BANCOR_PURCHASE, BANCOR_CHANGER
from one_frontrun import CHANGE_METHOD, CHANGE_SIGNATURE
from one_frontrun import BANCOR_TOKEN, ETH_ERC20_TOKEN

TOTAL_RESERVE = 80e3  # Total Bancor reserve was 80K ETH at highest point.
ETH_PRICE = 270.0
BLOCK_JUL03 = 3970000
BLOCK_AUG03 = 4113664
WEI_TO_ETH = 1e-18
BNT_TO_ETH = 1e-2


def get_tx_value_in_eth(tx):
  if tx[u'to'] == BANCOR_PURCHASE:
    return int(tx[u'value'], 16) * WEI_TO_ETH
  elif tx[u'to'] == BANCOR_CHANGER:
    try:
      method, from_token, to_token, amount, min_return = parse_tx_data(
          tx[u'input'], CHANGE_SIGNATURE)
    except Exception:
      log('Error while parsing', tx[u'hash'])
      return 0.0
    if set([from_token, to_token]) != set(
        [int(BANCOR_TOKEN, 16),
         int(ETH_ERC20_TOKEN, 16)]):
      log('Wrong from/to addresses', tx[u'hash'])
      return 0.0
    receipt = send_request({
        'method': 'eth_getTransactionReceipt',
        'params': [tx[u'hash']]
    })
    if not receipt[u'logs']:
      # log('Invalid or failed transaction', tx[u'hash'])
      return 0.0
    if from_token == int(ETH_ERC20_TOKEN, 16):
      return amount * WEI_TO_ETH
    else:
      return amount * WEI_TO_ETH * BNT_TO_ETH
  else:
    return 0.0


def run_simulation():
  total_txs = 0
  large_tx_values = []
  one_percent = (BLOCK_AUG03 - BLOCK_JUL03) / 100
  for block_number in xrange(BLOCK_JUL03, BLOCK_AUG03):
    if (block_number - BLOCK_JUL03) % one_percent == 0:
      log('{0}% done'.format((block_number - BLOCK_JUL03) / one_percent))
    block = send_request({
        'method': 'eth_getBlockByNumber',
        'params': [hex(block_number), True]
    })
    for tx in block[u'transactions']:
      value = get_tx_value_in_eth(tx)
      if value > 0:
        total_txs += 1
      if value > 99.0:
        log('Found a large transaction', value, tx[u'hash'])
        large_tx_values.append(value)

  log('All large TX values:', large_tx_values)
  log('Total TXs for BancorPurchase+BancorChanger', total_txs)
  log('Large TXs for BancorPurchase+BancorChanger', len(large_tx_values))
  total_roi = sum(large_tx_values) / TOTAL_RESERVE
  log('ROI for front-running all transaction >= 100 ETH: {0}%'.format(
      total_roi * 100))
  log('With a principal of 100 ETH, that would make you {0}$'.format(
      100.0 * total_roi * ETH_PRICE))


if __name__ == '__main__':
  run_simulation()

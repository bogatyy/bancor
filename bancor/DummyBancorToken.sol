pragma solidity ^0.4.11;

import './BasicERC20Token.sol';
import './BancorFormula.sol';

contract DummyBancorToken is BasicERC20Token, BancorFormula {

    string public standard = 'Token 0.1';
    string public name = 'Dummy Constant Reserve Rate Token';
    string public symbol = 'DBT';
    uint8 public decimals = 18;
    uint256 public totalSupply = 0;

    uint8 public ratio = 10; // CRR of 10%

    address public owner;

    uint256 public reserve_ratio_before;
    uint256 public reserve_ratio_after;

    /* I can't make MyEtherWallet send payments as part of constructor calls
     * while creating contracts. So instead of implementing a constructor,
     * we follow the SetUp/TearDown paradigm
    function setUp(uint256 _initialSupply) payable {
        owner = msg.sender;
        balances[msg.sender] = _initialSupply;
        totalSupply = _initialSupply;
    }

    function tearDown() {
        if (msg.sender != owner) return;
        selfdestruct(owner);
    }

    function reserveBalance() constant returns (uint256) {
        return this.balance;
    }

    // Our reserve token is always ETH.
    function deposit() payable returns (bool success) {
        if (msg.value == 0) return false;
        // Debug: check ratio before.
        reserve_ratio_before = totalSupply / (reserveBalance() - msg.value);
        uint256 tokensPurchased = calculatePurchaseReturn(totalSupply, reserveBalance(), ratio, msg.value);
        balances[msg.sender] += tokensPurchased;
        totalSupply += tokensPurchased;
        // Debug: check ratio after.
        reserve_ratio_after = totalSupply / reserveBalance();
        return true;
    }

    function withdraw(uint256 amount) returns (bool success) {
        if (balances[msg.sender] < amount) return false;
        // Debug: check ratio before.
        reserve_ratio_before = totalSupply / reserveBalance();
        uint256 ethAmount = calculateSaleReturn(totalSupply, reserveBalance(), ratio, amount);
        // Debug: check ratio after.
        reserve_ratio_after = (totalSupply - amount) / (reserveBalance() - ethAmount);
        balances[msg.sender] -= amount;
        totalSupply -= amount;
        if (!msg.sender.send(amount)) {
            balances[msg.sender] += amount;
            totalSupply += amount;
            return false;
        }
        return true;
    }

}


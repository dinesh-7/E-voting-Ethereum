from web3 import Web3
import json
import sys

def Ass_vote(addr,abi):
    w3=Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545")) 
    # with open('Compiled_code.json','r') as f:
    #     print(f)
    #     abi=f["contracts"]["sorting.sol"]["Ballot2"]["abi"]
    sorting_contract=w3.eth.contract(address=addr,abi=abi)
    
    '''
    When I deploy the contract, I choose the first account as the contract constructor--->w3.eth.accounts[0],
    and initalize 3 options with 3 leaders --->w3.eth.accounts[1],w3.eth.accounts[2],w3.eth.accounts[3]
   
    So I set the voters from 4th account,here I simply set 5 voters, you are free to choose more voters, but be attention not to exceed the number of nodes in Ganache test
    environment...
    '''
    num_voters=5
    names=['a','b','c','d','e'] #simple example
    print('Start assigning votes to voters...')
    for i in range(4,num_voters+4):
        sorting_contract.functions.Give_right_to_voters(w3.eth.accounts[i],names[i-4]).transact(transaction={'from':w3.eth.accounts[0]})
    print('Assignment Done!')
    return w3,sorting_contract


from solcx import compile_standard, install_solc
from ass_vote2 import Ass_vote
from flask import Flask, render_template, request, redirect, send_from_directory
from collections import defaultdict
from dotenv import load_dotenv
from web3 import Web3
import json
import time
import os
import sys

load_dotenv()

with open("./sorting.sol", "r") as file:
    sorting_file = file.read()
    # print(simple_storage_file)
print("Installing...")
install_solc("0.8.0")  # here we are installing the solidity complier with we want
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"sorting.sol": {"content": sorting_file}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.8.0",
)
# print(compiled_sol)

with open("Compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)

# now we need byte code and the abi to intract with the contract so we will take that part alone from the json or that compiled_sol variable
bytecode = compiled_sol["contracts"]["sorting.sol"]["Ballot2"]["evm"][
    "bytecode"
][
    "object"
]  # this is the same what we will get in the remix
abi = compiled_sol["contracts"]["sorting.sol"]["Ballot2"]["abi"]
# with open('abi2.json','r') as f:
#     abi=json.load(f)
# print(bytecode,abi)

# now we are going to connect to ganache our local blockchain network like Javascript VM or RemixVM london
ganachelink = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
chain_id = 1337
myadress = "0x1365397C460192c01d9c3fEc0371C860e045EB58"
# myprivatekey = 0xae1284e2d786daa2188125ed57ef7e58079eda7d29520bff6d189b4e28d9f4f9 # but you should not ues your private key like this in code anyone can see that
private_key = os.getenv(
    "Private_key"
)  # this is by adding the privatekey in the environment varible we did with .env file
print(private_key)

# ********************************************Contract Creation*************************************************************************

# till now we compiled the contract so now create the contract with abi and bytecode
Sorting = ganachelink.eth.contract(abi=abi, bytecode=bytecode)
# we need nonce for mining each and every transactions so we need to create that value actually we need it for authentication
nonce = ganachelink.eth.getTransactionCount(myadress)
# print(nonce)
# To deploy the contract or to send any transaction you need to do this , if you are going to change any state in the blockchain network
# 1.first you need to create a transaction
# 2.Sign the transaction with your private key
# 3.send the transaction to the network
# 1.create

deploy_transaction = Sorting.constructor(["Dinesh","Kalpana","Niveditha"],["0xc9BB8676f2328168B598Fe7578f45d572301B6E9","0x19Bc1CB5Ce6609Fe441f70B083Af3406aa6Fd750","0xFaB2C133074DA83AA7297200CD3588F092FAc384"],1,2).buildTransaction(
    {
        "chainId": chain_id,
        "gasPrice": ganachelink.eth.gas_price,
        "from": myadress,
        "nonce": nonce,
    }
)
# 2.sign
signed_txn = ganachelink.eth.account.sign_transaction(
    deploy_transaction, private_key=private_key
)
# 3.send it to the Blockchain network
contract_hash = ganachelink.eth.send_raw_transaction(signed_txn.rawTransaction)
contract_recipt = ganachelink.eth.wait_for_transaction_receipt(contract_hash)
print("done! Contract deployed at ,", contract_recipt.contractAddress)
# print(contract_recipt)

# contract_addr = sys.argv[1]
contract_addr = contract_recipt.contractAddress
w3, sorting_contract = Ass_vote(contract_addr,abi)
# print(sorting_contract.functions.winnerName())
vote_app2 = Flask(__name__, static_folder="static2", template_folder="templates2")


@vote_app2.route("/")
def welcome():
    return render_template("content.html")


@vote_app2.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(vote_app2.root_path, "static2"), "favicon.ico"
    )


@vote_app2.route("/ballot_status.html")
def ballot_status():
    # voter_info
    num_voters = sorting_contract.functions.num_voters().call()
    voter_addrs = [
        sorting_contract.functions.Valid_voter_address(i).call()
        for i in range(num_voters)
    ]
    voter_names = [
        sorting_contract.functions.voters(addr).call()[2] for addr in voter_addrs
    ]
    # option_info
    num_options = sorting_contract.functions.num_options().call()
    options = [sorting_contract.functions.Options(i).call() for i in range(num_options)]

    res = defaultdict(dict)
    for name in voter_names:
        for option in options:
            res[name + "-" + option][
                "voter2option"
            ] = sorting_contract.functions.voter_option_match(name, option).call()[1]
            res[name + "-" + option][
                "option2voter"
            ] = sorting_contract.functions.option_voter_match(option, name).call()[1]

    res_list = [[k, sum(v.values())] for k, v in res.items()]
    return render_template("ballot_status.html", data=res_list)


@vote_app2.route("/login.html", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html", error_message="")
    # POST
    tp = request.form.get("type")
    if not tp:
        return render_template(
            "login.html", error_message="Please select your identity first!"
        )
    else:
        addr = request.form.get("Address")
        # voter
        if tp == "voter":
            # all authorized voters' addresses
            num_voters = sorting_contract.functions.num_voters().call()
            authorized_addrs = [
                sorting_contract.functions.Valid_voter_address(i).call()
                for i in range(num_voters)
            ]

            if addr not in authorized_addrs:
                return render_template(
                    "login.html", error_message="You have no right to vote!"
                )
            else:
                current_voter = sorting_contract.functions.voters(addr).call()
                if time.time() > sorting_contract.functions.deadline().call():
                    print("the position voter won with {} votes".format(sorting_contract.functions.winningProposal().call()))
                    return render_template(
                        "login.html", error_message="The ballout is over! and the Winner Name is {}" .format(sorting_contract.functions.winnerName().call())
                    )
                elif current_voter[1] == True:
                    return render_template(
                        "login.html", error_message="You have already voted!"
                    )
                else:
                    redirect_addr = "/voter/" + addr
                    return redirect(redirect_addr)
        # leader
        num_leaders = sorting_contract.functions.num_options().call()
        leaders = [
            sorting_contract.functions.leader_address(i).call()
            for i in range(num_leaders)
        ]
        if addr not in leaders:
            return render_template(
                "login.html", error_message="You are not legal leader!"
            )
        else:
            current_leader = sorting_contract.functions.Leaders(addr).call()
            if time.time() > sorting_contract.functions.deadline().call():
                print("the position voter won with {} votes".format(sorting_contract.functions.winningProposal().call()))
                return render_template(
                    "login.html", error_message="The ballout is over! and the Winner Name is {}" .format(sorting_contract.functions.winnerName().call())
                )
            elif current_leader[2] == True:
                return render_template(
                    "login.html", error_message="You have already voted!"
                )
            else:
                redirect_addr = "/leader/" + addr
                return redirect(redirect_addr)


@vote_app2.route("/voter/<addr>", methods=["POST", "GET"])
def voter_vote(addr):
    num_options = sorting_contract.functions.num_options().call()
    option_names = [
        sorting_contract.functions.Options(i).call() for i in range(num_options)
    ]

    if request.method == "GET":
        return render_template("voter_vote.html", data=option_names, error_message="")
    # receive post
    vote_info = {}
    for opt in option_names:
        point = request.form.get(opt)
        if point:
            if not point.isdigit():
                return render_template(
                    "voter_vote.html",
                    data=option_names,
                    error_message="Wrong input type,Only integers are accepted!",
                )
            elif int(point) > 0:
                vote_info[opt] = int(point)

    option_names, point_allocation = list(vote_info.keys()), list(vote_info.values())
    print("Printing what is going inside the vote contract " ,option_names,point_allocation)
    voter_info = sorting_contract.functions.voters(addr).call()
    num_points_given = voter_info[0]
    if sum(point_allocation) != num_points_given:
        return render_template(
            "voter_vote.html",
            data=option_names,
            error_message="You have {} points totally!".format(num_points_given),
        )
    else:
        vote_yet = voter_info[1]
        if vote_yet:
            return render_template(
                "voter_vote.html",
                data=option_names,
                error_message="You have already voted!",
            )
        sorting_contract.functions.Vote(
            option_names=option_names, point_allocation=point_allocation
        ).transact(transaction={"from": addr})
        print(sorting_contract.functions.winnerName().call())
        print(sorting_contract.functions.winningProposal().call())
        return render_template("vote_done.html")


@vote_app2.route("/leader/<addr>", methods=["POST", "GET"])
def leader_vote(addr):
    # leader_info
    leader_info = sorting_contract.functions.Leaders(addr).call()

    # voter_addrs
    voter_count = sorting_contract.functions.num_voters().call()
    voter_addrs = [
        sorting_contract.functions.Valid_voter_address(i).call()
        for i in range(voter_count)
    ]

    name2addr = {}  # name-->address
    for addr in voter_addrs:
        name = sorting_contract.functions.voters(addr).call()[2]
        name2addr[name] = addr

    if request.method == "GET":
        return render_template(
            "leader_vote.html", data=list(name2addr.keys()), error_message=""
        )
    vote_info = {}  # name-->point
    for name in list(name2addr.keys()):
        point = request.form.get(name)
        if point:
            if not point.isdigit():
                return render_template(
                    "leader_vote.html",
                    data=list(name2addr.keys()),
                    error_message="Wrong input type,Only integers are accepted!",
                )
            elif int(point) > 0:
                vote_info[name] = int(point)

    addr_list = []  # voter address list
    point_assign_list = []
    for k, v in vote_info.items():
        addr_list.append(name2addr[k])
        point_assign_list.append(v)

    num_points_given = leader_info[1]
    if sum(point_assign_list) != num_points_given:
        return render_template(
            "leader_vote.html",
            data=list(name2addr.keys()),
            error_message="You have {} points totally!".format(num_points_given),
        )
    else:
        assign_yet = leader_info[2]


        if assign_yet:
            return render_template(
                "leader_vote.html",
                data=list(name2addr.keys()),
                error_message="You have already assigned!",
            )
        print("Address list & point assignment list",addr_list,point_assign_list)
        sorting_contract.functions.Vote_leader(addr_list, point_assign_list).transact(
            transaction={"from": leader_info[3]}
        )
        print(sorting_contract.functions.winnerName().call())
        print(sorting_contract.functions.winningProposal().call())

        return render_template("vote_done.html")



if __name__ == "__main__":
    vote_app2.run()

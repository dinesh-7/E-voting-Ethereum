// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8;

contract Ballot2 {
    struct Voter {
        uint256 voter_points; // totally z points
        bool voted; // whether or not voted
        string name; // name of voter
        string[] preferred_option_names; //voted to which options
        uint256 vote; //// index of the voted proposal from remix default ballot
    }
    struct Leader {
        string option_name; //corresponding option
        uint256 leader_points; //total y points
        bool assigned; //whether or not assigned to voters
        address leader_addr;
        address[] assign_voters; //assign to which voters
    }

    struct Option {
        string name; //name of option
        uint256 count; //number of accumulated votes
    }

    struct vv {
        string name;
        uint256 count;
    }

    //from Ballot remix default
    struct Proposal {
        // If you can limit the length to a certain number of bytes,
        // always use one of bytes1 to bytes32 because they are much cheaper
        string name; // short name (up to 32 bytes)
        uint256 voteCount; // number of accumulated votes
    }
    Proposal[] public proposals;

    mapping(string => mapping(string => Option)) public voter_option_match; //mapping between voters and options
    mapping(string => mapping(string => vv)) public option_voter_match;

    uint256 public deadline; //deadline of the voting
    address public chairperson; //promoter
    mapping(address => Voter) public voters; //voters
    mapping(address => Leader) public Leaders;
    uint256 public z; //fixed points assigned to each voter
    uint256 public y; //fixed points assigned to each project(option) leader
    string[] public Options; // store name of options
    address[] public Valid_voter_address; //separately store all the addresses of authorized voters
    address[] public leader_address;
    uint256 public num_options = 0; //record the number of options
    uint256 public num_voters = 0; //record the number of voters

    //new ballot
    constructor(
        string[] memory optionNames,
        address[] memory leaders,
        int256 points_per_voter,
        int256 points_per_leader
    ) {
        chairperson = msg.sender;
        //initial setting of Options
        for (uint256 i = 0; i < optionNames.length; i++) {
            Options.push(optionNames[i]); //insert name
            num_options++;
        }
        z = uint256(points_per_voter);
        y = uint256(points_per_leader);
        //initialize the leaders info
        for (uint256 i = 0; i < leaders.length; i++) {
            Leaders[leaders[i]].option_name = optionNames[i];
            Leaders[leaders[i]].leader_points = y;
            Leaders[leaders[i]].assigned = false;
            Leaders[leaders[i]].leader_addr = leaders[i];

            leader_address.push(leaders[i]); //store the leader address separately
        }
        for (uint256 i = 0; i < optionNames.length; i++) {
            // 'Proposal({...})' creates a temporary
            // Proposal object and 'proposals.push(...)'
            // appends it to the end of 'proposals'.
            proposals.push(Proposal({name: optionNames[i], voteCount: 0}));
        }
        deadline = block.timestamp + 5 * 60;
        // deadline = block.timestamp + 240 * 60 * 60; //once the voters have votes, the countdown starts, voters have to accomplish voting within one day.
    }

    function Give_right_to_voters(address voter, string memory name) public {
        require(msg.sender == chairperson); //must done by chairperson
        require(!voters[voter].voted);
        require(voters[voter].voter_points == 0);
        voters[voter].voter_points = z; //give voter N points for this new ballot
        voters[voter].name = name;

        Valid_voter_address.push(voter); //store the address
        num_voters++;

        //initialize the voter_group_match---for each voter, initally set vote count=0 for all options
        for (uint256 i = 0; i < num_options; i++) {
            voter_option_match[voters[voter].name][Options[i]].name = Options[
                i
            ];
            voter_option_match[voters[voter].name][Options[i]].count = 0;
        }

        for (uint256 i = 0; i < num_options; i++) {
            option_voter_match[Options[i]][voters[voter].name].name = voters[
                voter
            ].name;
            option_voter_match[Options[i]][voters[voter].name].count = 0;
        }
    }

    //do not use any state variable, so can be resitricted to pure
    function Sum(uint256[] memory point_allocation)
        public
        pure
        returns (uint256)
    {
        uint256 sum = 0;
        for (uint256 i = 0; i < point_allocation.length; i++) {
            sum += point_allocation[i];
        }
        return sum;
    }

    function compare_str(string memory str1, string memory str2)
        public
        pure
        returns (bool)
    {
        return
            keccak256(abi.encodePacked(str1)) ==
            keccak256(abi.encodePacked(str2));
    }

    function Vote(
        string[] memory option_names,
        uint256[] memory point_allocation
    ) public {
        //option_idx: voter's decision about to choose which options
        //point_allocation: how to allocation the N points to above options

        Voter storage v = voters[msg.sender]; // voter object

        // Voter storage v = voters[msg.sender]; // voter object
        require(block.timestamp < deadline, "Voting has finished!"); //should vote before deadline
        require(option_names.length == point_allocation.length);
        uint256 x;
        for (uint256 i = 0; i < option_names.length; i++) {
            bool within = false;
            for (uint256 j = 0; j < Options.length; j++) {
                if (compare_str(option_names[i], Options[j]) == true) {
                    within = true;
                    x = j;
                    break;
                }
            }
            require(within == true, "Non-existing option!");
        }
        //check whether the option_idx beyond the max possible option idx
        require(
            Sum(point_allocation) == v.voter_points,
            "Sum of your votes should be equal to z!"
        );
        //the sum of voter's point allocation must equal points assigned to him/her
        require(!v.voted, "You have already voted!");
        v.voted = true;
        v.preferred_option_names = option_names;
        v.vote = x;

        // this code is from remix basic ballot
        // If 'proposal' is out of the range of the array,
        // this will throw automatically and revert all
        // changes.
        proposals[x].voteCount += v.voter_points;

        for (uint256 i = 0; i < option_names.length; i++) {
            // Need to split points before storing
            voter_option_match[v.name][option_names[i]]
                .count += point_allocation[i];
            v.preferred_option_names.push(option_names[i]);
        }
    }

    function Vote_leader(
        address[] memory prefer_voters,
        uint256[] memory point_assignment
    ) public {
        Leader storage l = Leaders[msg.sender];

        require(block.timestamp < deadline, "Time is over!"); //should assign before deadline
        require(prefer_voters.length == point_assignment.length);
        for (uint256 i = 0; i < prefer_voters.length; i++) {
            bool valid_voter = false;
            for (uint256 j = 0; j < Valid_voter_address.length; j++) {
                if (prefer_voters[i] == Valid_voter_address[j]) {
                    valid_voter = true;
                    break;
                }
            }
            require(valid_voter = true, "Non-existing voter!");
        }
        require(
            Sum(point_assignment) == l.leader_points,
            "Sum of your assign points should be equal to y!"
        );
        require(!l.assigned, "You have already assigned!");
        l.assigned = true;
        l.assign_voters = prefer_voters;
        for (uint256 i = 0; i < prefer_voters.length; i++) {
            // from remix default ballot
            Voter storage delegate_ = voters[prefer_voters[i]];
            if (delegate_.voted) {
                // If the delegate already voted,
                // directly add to the number of votes
                proposals[delegate_.vote].voteCount += l.leader_points;
            } else {
                // If the delegate did not vote yet,
                // add to her weight.
                delegate_.voter_points += l.leader_points;
            }
        }

        for (uint256 i = 0; i < prefer_voters.length; i++) {
            option_voter_match[l.option_name][voters[prefer_voters[i]].name]
                .count += point_assignment[i];
        }
    }

    function winningProposal()
        public
        view
        returns (uint256 winningProposal_, uint256 has_vote_count)
    {
        uint256 winningVoteCount = 0;
        for (uint256 p = 0; p < proposals.length; p++) {
            if (proposals[p].voteCount > winningVoteCount) {
                winningVoteCount = proposals[p].voteCount;
                winningProposal_ = p;
                has_vote_count = winningVoteCount;
            }
        }
    }

    /**
     * @dev Calls winningProposal() function to get the index of the winner contained in the proposals array and then
     * @return winnerName_ the name of the winner
     */
    function winnerName() public view returns (string memory winnerName_) {
        uint256 position;
        uint256 vote_count;
        (position, vote_count) = winningProposal();
        winnerName_ = proposals[position].name;
    }
}

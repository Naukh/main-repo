#include <iostream>
#include <vector>
#include <unordered_map>

using namespace std;

// Create hash table
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> hash;
        for (int i = 0; i < nums.size(); i++) {
            hash[nums[i]] = i;
        }

        for (int i = 0; i < nums.size(); i++) {
            int complement = target - nums[i];

            if (hash.find(complement) != hash.end() && hash[complement] != i) {
                std::cout << "Key is: " << hash[complement] << " and Value is: " << complement << std::endl;
                return {i, hash[complement]};
            }
        }
        return {};
    }
};

// Create one pass has table
class OnePass {
public:
    vector<int> twoSum(vector<int>& nums, int target){
        unordered_map<int, int> hash;
        for (int i =0; i<nums.size();++i){
            int complement = target - nums[i];
            auto it = hash.find(complement);

            if (it != hash.end()){
                std::cout << "Key is: " << hash[complement] << " and Value is: " << complement << std::endl;
                std::cout << "Found: key = " << it->first << ", value = " << it->second << std::endl;
                return {hash[complement], i};
            }
            hash[nums[i]] = i;
        }
        return {};
    }
};

int main() {
    vector<int> nums = {1, 2, 5, 7, 9};
    int target = 12;

    // Solution sol;
    OnePass sol;
    vector<int> result = sol.twoSum(nums, target);

    if (!result.empty()) {
        cout << "Indices: " << result[0] << ", " << result[1] << endl;
        cout << "Sum of Values: " << nums[result[0]] << ", " << nums[result[1]] << " results in TARGET: " << target << endl;
    } else {
        cout << "No two numbers found that add up to target." << endl;
    }

    return 0;
}
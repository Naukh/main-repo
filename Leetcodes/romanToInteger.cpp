#include <iostream>
#include <unordered_map>
#include <string>
#include <unordered_set>
#include <stdexcept>  // for std::invalid_argument

using namespace std;

class Solution
{
public:
    int romanToInt(const string& s)
    {
        static const unordered_map<char, int> roman = {
            {'I', 1}, 
            {'V', 5}, 
            {'X', 10}, 
            {'L', 50}, 
            {'C', 100}, 
            {'D', 500}, 
            {'M', 1000}
        };

        if (s.empty())
            throw invalid_argument("Empty Roman numeral string");

        // Validate all characters first
        for (char c : s) {
            if (roman.find(c) == roman.end())
                throw invalid_argument("Invalid Roman numeral character");
        }

        // Validate repetition and subtraction rules
        if (!isValidRoman(s))
            throw invalid_argument("Invalid Roman numeral syntax");

        int res = 0;
        size_t n = s.size();

        for (size_t i = 0; i < n - 1; i++)
        {
            if (roman.at(s[i]) < roman.at(s[i + 1]))
                res -= roman.at(s[i]);
            else
                res += roman.at(s[i]);
        }
        return res + roman.at(s.back());
    }

private:
    bool isValidRoman(const string& s)
    {
        // Characters that cannot repeat
        static const unordered_set<char> noRepeat = {'V', 'L', 'D'};

        int repeatCount = 1;

        for (size_t i = 1; i < s.size(); ++i)
        {
            if (s[i] == s[i - 1])
            {
                repeatCount++;
                // Check if this char cannot be repeated
                if (noRepeat.count(s[i]) > 0)
                    return false;
                // Check if repeated more than 3 times
                if (repeatCount > 3)
                    return false;
            }
            else
            {
                repeatCount = 1;
            }
        }

        // Validate subtraction rules:
        // Only these pairs are allowed:
        // I before V or X
        // X before L or C
        // C before D or M

        for (size_t i = 0; i < s.size() - 1; ++i)
        {
            int curr = romanValue(s[i]);
            int next = romanValue(s[i + 1]);

            if (curr < next)
            {
                // Check valid subtraction pairs
                char c = s[i];
                char n = s[i + 1];

                if (c == 'I' && (n == 'V' || n == 'X'))
                    continue;
                else if (c == 'X' && (n == 'L' || n == 'C'))
                    continue;
                else if (c == 'C' && (n == 'D' || n == 'M'))
                    continue;
                else
                    return false;
            }
        }

        return true;
    }

    int romanValue(char c)
    {
        switch (c)
        {
            case 'I': return 1;
            case 'V': return 5;
            case 'X': return 10;
            case 'L': return 50;
            case 'C': return 100;
            case 'D': return 500;
            case 'M': return 1000;
            default: return 0;  // Should never happen if input validated
        }
    }
};


int main()
{
    int value = 0;
    string romanValue;

    // Solution sol;
    Solution sol;
    
    romanValue = "III";
    value = sol.romanToInt(romanValue);
    std::cout << "The roman numeral is: " << romanValue << ", The integer is: " << value << std::endl;

    romanValue = "LVIII";
    value = sol.romanToInt(romanValue);
    std::cout << "The roman numeral is: " << romanValue << ", The integer is: " << value << std::endl;

    romanValue = "MCMXCIV";
    value = sol.romanToInt(romanValue);
    std::cout << "The roman numeral is: " << romanValue << ", The integer is: " << value << std::endl;

    romanValue = "IV";
    value = sol.romanToInt(romanValue);
    std::cout << "The roman numeral is: " << romanValue << ", The integer is: " << value << std::endl;

    // romanValue = "IIII";
    // value = sol.romanToInt(romanValue);
    // std::cout << "The roman numeral is: " << romanValue << ", The integer is: " << value << std::endl;


    return 0;
}
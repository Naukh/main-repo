#include <iostream>
class Solution
{
public:
    bool isPalindrome(int x)
    {
        // Negative number and number ending with zero with exception of zero only can't be palindrome
        if (x < 0 || (x % 10 == 0 && x != 0))
        {
            return false;
        }

        int reversedHalf = 0;

        while (x > reversedHalf)
        {
            reversedHalf = reversedHalf * 10 + x % 10;
            x /= 10;
        }
        // For odd length numbers ignore the middle digit by reversedHalf by 10
        return (x == reversedHalf || x == reversedHalf / 10);
    }
};

int main()
{
    Solution sol;
    int testCases[] = {121, -121, 10, 12321, 0, 1221, 1001};

    for (int x : testCases)
    {
        std::cout << "isPalindrome(" << x << ") = "
                  << (sol.isPalindrome(x) ? "true" : "false") << std::endl;
    }

    return 0;
}
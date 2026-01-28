class Solution:
    def longestPalindrome(self, s: str) -> str:
        if s is None or len(s) == 0:
            return ""
        else:
            _start = 0
            _end = 0
            for i in range(len(s)):
                _len1 = self.expand_around_center(s, i, i)      # "racecar"
                _len2 = self.expand_around_center(s, i, i+1)    # "abba"
                _len = max(_len1, _len2)
                if _len > _end - _start:
                    _start = i - (_len - 1) // 2
                    _end = i + _len // 2

        return s[_start:_end+1]

    def expand_around_center(self, s: str, left: int, right: int) -> int:
        _left = left
        _right = right
        print(f"\nstarting left={_left}, right={_right}")
        while _left >= 0 and _right < len(s) and s[_left] == s[_right]:
            print(f"\ts[{_left}]={s[_left]}, s[{_right}]={s[_right]}")
            _left -= 1
            _right += 1
        print(f"exiting left={_left}, right={_right}, return={_right - _left - 1}")
        return _right - (_left + 1)


class SolutionClean:
    def longestPalindrome(self, s: str) -> str:
        if s is None or len(s) == 0:
            return ""
        else:
            _start = 0
            _end = 0
            for i in range(len(s)):
                _len1 = self.expand_around_center(s, i, i)      # "racecar"
                _len2 = self.expand_around_center(s, i, i+1)    # "abba"
                _len = max(_len1, _len2)
                if _len > _end - _start:
                    _start = i - (_len - 1) // 2
                    _end = i + _len // 2

        return s[_start:_end+1]

    def expand_around_center(self, s: str, left: int, right: int) -> int:
        _left = left
        _right = right
        while _left >= 0 and _right < len(s) and s[_left] == s[_right]:
            _left -= 1
            _right += 1
        return _right - (_left + 1)


class SolutionBruteForce(object):
    def longestPalindrome(self, s):
        """
        :type s: str
        :rtype: str
        """
        split = list(s)
        sub = ""
        long = ""
        for x in range(len(s), 0, -1):
            c = 0
            while c + x <= len(s):
                temp = s[c:c+x]
                if temp == temp[::-1]:
                    return temp
                print(temp)
                c += 1


obj_brute_force = SolutionBruteForce()
print(obj_brute_force.longestPalindrome("az_abba"))

# obj = Solution()
# print(obj.longestPalindrome("abba"))
# print(obj.longestPalindrome("racecar"))
pass

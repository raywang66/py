class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        answer = 0

        # Because searching is inevitable, it'll be better to use hashable data type
        # Python dicts are hashmaps, so if we use all characters of the string, searching
        # in keys will be fast
        # (key, value) "key" is the character, and "value" is it's index

        # The question just asks for "the length of the longest substring without repeating characters".
        # It does not ask for the actual substring, so we just need to remember the length of
        # longest substring
        char_index_dict = {}

        i = 0
        for j in range(len(s)):
            if s[j] in char_index_dict:
                i = max(char_index_dict[s[j]], i)

            answer = max(answer, j - i + 1)
            char_index_dict[s[j]] = j + 1

        return answer

# a = Solution()
# print(a.lengthOfLongestSubstring("abcabcbb"))


class SomeClass:

    """
    drivers is a class variable. It's declared inside the class but outside of any of
    the instance methods.  It's not tied to any particular object of the class, hence
    shared across all the objects of the class. Modifying a class variable affects all
    objects instance at the same time.
    """
    drivers = []

    def __init__(self, param1, param2):
        self.instance_var1 = param1
        # instance_var1 is a instance variable
        self.instance_var2 = param2
        # instance_var2 is a instance variable

    def add_driver(self, driver_name = ""):
        SomeClass.drivers.append(driver_name)


print("instantiate obj1")
obj1 = SomeClass("first instance", 18)
print(len(obj1.drivers))
obj1.drivers.append("added by obj1")

print("instantiate obj2")
obj2 = SomeClass("second instance", 25)
print(len(obj2.drivers))
print(obj2.drivers[0])
obj2.add_driver("added by obj2")

print("back to obj1")
print(len(obj1.drivers))
print(obj1.drivers)

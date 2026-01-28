class Solution:
    def coin_change(self, coins, amount):
        dp = [amount + 1] * (amount + 1)
        dp[0] = 0

        for a in range(1, amount + 1):
            for c in coins:
                if a - c >= 0:
                    dp[a] = min(dp[a], 1 + dp[a - c])

        return dp[amount] if dp[amount] != amount + 1 else -1


# cc = Solution()
# print(cc.coin_change([1, 3, 4, 5], 7))

x = ['A', 'B', 'C']
for i, item in enumerate(x):
    x.pop(i)
    print(i, item)
print(x)

tickets = [["JFK", "SFO"], ["JFK", "ATL"], ["SFO", "ATL"], ["ATL", "JFK"], ["ATL", "SFO"]]
my_dict = dict()
for i, v in enumerate(tickets):
    if v not in my_dict.keys():
        my_dict[v] = []
    else:
        my_dict[v].append(v)



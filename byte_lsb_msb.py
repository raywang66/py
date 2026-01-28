def rev_bytes_32bits(x):
    x = (x & 0x00FF00FF) << 8 | (x & 0xFF00FF00) >> 8
    x = (x & 0x0000FFFF) << 16 | (x & 0xFFFF0000) >> 16
    # x = x << 16 | x >> 16
    return x


orig_x = 0xE6_A2_C4_80
# print("{:#08x}".format(x))
print(f"0x{orig_x:08X}")

rev_x = rev_bytes_32bits(orig_x)
# print("{:#08x}".format(rev_x))
print(f"0x{rev_x:08X}")

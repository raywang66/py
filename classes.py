class Singleton:
    __instance = None

    def __new__(cls, *args):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls, *args)
        return cls.__instance


class Human:

    def __init__(self, age=0, name='Someone'):
        self.age = age
        self.name = name
        pass


class Man(Human):
    pass


class Woman(Human):
    pass


m1 = Man()
m2 = Man()
if m1 != m2:
    print('m1 and m2 are two different objects')
else:
    print('m1 and m2 are the same object')

s1 = Singleton()
s2 = Singleton()
if s1 != s2:
    print('s1 and s2 are two different objects')
else:
    print('s1 and s2 are the same object')


def Maxx_round(mp):
    num_qdb = int(mp/0.25)
     if (abs(mp) % 0.25) >= (0.25/2):
             if mp < 0:
                     num_qdb -= 1
             else:
                     num_qdb += 1
     return num_qdb


def Ray_round(mp):
    num_qdb = int(mp*4)
     if (abs(mp) % 0.25) >= (0.25/2):
             if mp < 0:
                     num_qdb -= 1
             else:
                     num_qdb += 1
     return num_qdb


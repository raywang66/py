# Saved as timer.py
import time

## Create the variable _TIME from sys.argv or wherever, make sure it is a valid float, > 0, etc etc
## Depends on how you expect input

_TIME = 10  # Just for example, remove this

while _TIME > 0:
    m, s = divmod(_TIME, 60)
    h, m = divmod(m, 60)
    if False:
        print(f"\r{int(h)}".rjust(3,'0'), f"{int(m)}".rjust(2,'0'),
              f"{s:.3f}".rjust(5,'0'), sep=':', end='')
    else:
        print(f"\r{int(h):03}:{int(m):02}:{s:05.3f}", end='')

    _TIME -= 0.1
    time.sleep(0.1)
else:
    print("\r  Completed !  ")

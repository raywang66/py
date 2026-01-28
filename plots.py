import matplotlib.pyplot as plt
import numpy as np

# Some example data to display
x = np.linspace(0, 2 * np.pi, 400)
y = np.sin(x ** 2)

col = 2
row = 4


fig, axs = plt.subplots(row, col)
for i in range(row):
    for j in range(col):
        axs[i, j].plot(x, y)
        axs[i, j].plot(x, y*2)
        axs[i, j].plot(x, y/2)
        axs[i, j].set_title(f'Axis [{i}, {j}]')

# axs[0, 0].plot(x, y)
# axs[0, 0].set_title('Axis [0, 0]')
# axs[0, 1].plot(x, y, 'tab:orange')
# axs[0, 1].set_title('Axis [0, 1]')
# axs[1, 0].plot(x, -y, 'tab:green')
# axs[1, 0].set_title('Axis [1, 0]')
# axs[1, 1].plot(x, -y, 'tab:red')
# axs[1, 1].set_title('Axis [1, 1]')

# for ax in axs.flat:
#    ax.set(xlabel='x-label', ylabel='y-label')

# Hide x labels and tick labels for top plots and y ticks for right plots.
# for ax in axs.flat:
#    ax.label_outer()

fig.show()
input("Press any key to continue...")

import numpy as np
import matplotlib.pyplot as plt
left, width = 0.1, 0.8
rect1 = [left, 0.65, width, 0.25]  # left, bottom, width, height
rect2 = [left, 0.4, width, 0.25]
rect3 = [left, 0.1, width, 0.3]

fig = plt.figure(figsize=(10, 6))

ax1 = fig.add_axes(rect1)
ax2 = fig.add_axes(rect2, sharex=ax1)
ax3 = fig.add_axes(rect3, sharex=ax1)

x = np.linspace(0, 6.5*np.pi, 200)
y1 = np.sin(x)
y2 = np.sin(2*x)

ax1.plot(x, y1, color='b', lw=2)
ax2.plot(x, y2, color='g', lw=2)
ax3.plot(x, y1+y2, color='r', lw=2)

ax3.get_xaxis().set_ticks([])

# for ax in [ax1, ax2, ax3]:
#     ax.hlines(0, 0, 6.5*np.pi, color='black')
#     for key in ['right', 'top', 'bottom']:
#         ax.spines[key].set_visible(False)
#
# plt.xlim(0, 6.6*np.pi)
# ax3.text(2, 0.9, 'Sum signal', fontsize=14)
plt.show()

#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
DATA = [
    23,
    17,
    27,
    21,
    25,
    22,
    30,
    30,
    23,
    18,
]
mpl.rcParams['text.usetex'] = True
mpl.rcParams['text.latex.unicode'] = True
mpl.rcParams['axes.unicode_minus'] = False
mpl.rcParams['font.family'] = 'Times-Roman'
plt.rc('text', usetex = True)
plt.rc('text.latex', preamble=r'\usepackage{cmbright}')
plt.rc('font', size = 10.5)
figure = plt.figure(figsize = (6.2, 4))
# plt.title(title)
plt.bar(np.arange(1, 11), DATA, color='#00C0FF')
plt.xlim((0.4,11.4))
plt.xticks(np.arange(1.4,11.4), np.arange(1,11))
plt.yticks(np.arange(0,40,5), np.arange(0,40,5))
plt.ylim((0, 35))
plt.tight_layout()
plt.savefig('BlockDistribute.pdf', format = 'pdf')

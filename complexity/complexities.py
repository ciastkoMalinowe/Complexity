import numpy as np


# set of functions representing computational complexities
class Complexity:
    def n(x, a):
        return a * x

    def n_log_n(x, a):
        return a * x * np.log2(x)

    def n_power_2(x, a):
        return x * x * a

    def log_n(x, a):
        return a * np.log2(x)

    def sqrt_n(x, a):
        return a * np.sqrt(x)

    def n_power_3(x, a):
        return a * x * x * x

    def exponential(x, a):
        return np.exp2(x) * a

    def const(x, a):
        arr = np.empty(x.shape)
        arr.fill(a)
        return arr

    all = [const, log_n, sqrt_n, n, n_log_n, n_power_2, n_power_3, exponential]
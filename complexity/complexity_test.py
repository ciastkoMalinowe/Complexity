import logging
import time

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from .complexities import Complexity
from .timeout import Timeout as Timeout

# creating logger with handler to standard output and formatter
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

logger.addHandler(ch)


# decorator used to measure single performance function time (not in loop)
def single_test(before, after, timeout):
    def wrap(fun):
        logger.info("Created single_test decorator for given function")

        @Timeout(timeout)
        def test(n, *args, **kwargs):
            exec(before)
            start = time.perf_counter()
            fun(n, *args, **kwargs)
            end = time.perf_counter()
            exec(after)
            return end - start

        return test

    return wrap


# decorator used to measure average performance function time (in loop)
def multi_test(before, after, timeout, number):
    def wrap(fun):
        logger.info("Created multi_test decorator for given function")

        @Timeout(timeout)
        def test(n, *args, **kwargs):
            exec(before)
            time_sum = 0
            for i in range(1, number):
                start = time.perf_counter()
                fun(n, *args, **kwargs)
                end = time.perf_counter()
                time_sum += (end - start)
                exec(after)
            return time_sum / number

        return test

    return wrap


# class testing efficient computational complexity of given function
class ComplexityTester:
    def __init__(self, prepare, clean, algorithm, timeout=30, single_timeout=3, multi_timeout=2, loops=10):

        @single_test(prepare, clean, single_timeout)
        def single(n, *args, **kwargs):
            return algorithm(n, *args, **kwargs)

        @multi_test(prepare, clean, multi_timeout, loops)
        def multi(n, *args, **kwargs):
            return algorithm(n, *args, **kwargs)

        self.single_test = single
        self.multi_test = multi
        self.timeout = timeout
        self.complexity_fun = None
        self.complexity_fun_coefficients = None
        self.complexity_name = None
        self.x = None
        self.y = None

        logger.info("Started evaluating complexity of function")
        self.find_complexity()

    # chooses complexity which fits gathered samples
    def find_complexity(self):

        def compare_complexities(fun1, fun2):
            operands, err = self.test_complexity((lambda x, a, b: fun1(x, a) + fun2(x, b)), self.timeout)
            logger.info("Compared %s and %s", fun1.__name__, fun2.__name__)
            return 1 if operands[0] < operands[1] else -1

        def find(i):
            if i == len(Complexity.all) - 1:
                return i
            res = compare_complexities(Complexity.all[i], Complexity.all[i + 1])
            return i if res == -1 else find(i + 1)

        self.make_samples()
        result = find(0)
        self.complexity_fun = Complexity.all[result]
        self.complexity_fun_coefficients, error = self.test_complexity(self.complexity_fun, self.timeout)
        self.complexity_name = self.complexity_fun.__name__
        logger.info("Computational complexity estimated at %s", "O(" + self.complexity_fun.__name__ + ")")

    # measures time of function performance for various n
    def make_samples(self):

        @Timeout(self.timeout)
        def make_samples(x=[], y=[]):

            logger.info("Started testing in (1, 10)")
            for i in range(1, 10):
                try:
                    y.append(self.multi_test(i))
                    x.append(i)
                except Timeout.TimeoutException:
                    logger.warning("Function exceeded timeout for %d", i)
                    logger.info("Switch multi_test to single_test")
                    for j in range(i, 10):
                        try:
                            y.append(self.single_test(j))
                            x.append(j)
                        except Timeout.TimeoutException:
                            logger.warning("Function exceeded timeout for %d", j)
                            logger.warning("Due to number of samples result might by highly implausible.")
                    return x, y
            logger.info("Started testing in (10,100)")
            for i in range(11, 100, 10):
                try:
                    y.append(self.multi_test(i))
                    x.append(i)
                except Timeout.TimeoutException:
                    logger.warning("Function exceeded timeout for %d", i)
                    logger.info("Switch multi_test to single_test")
                    print(i)
                    for j in range(i, 100, 1):
                        try:
                            y.append(self.single_test(j))
                            x.append(j)
                        except Timeout.TimeoutException:
                            logger.warning("Function exceeded timeout for %d", j)
                            logger.warning("Due to number of samples result is likely to be underestimated")
                            x.append(j)
                            y.append(2.0)
                            return x, y
            logger.info("Started testing in (100,10000)")
            for i in range(101, 10000, 100):
                try:
                    y.append(self.multi_test(i))
                    x.append(i)
                except Timeout.TimeoutException:
                    logger.warning("Function exceeded timeout for %d", i)
                    return x, y
            return x, y

        try:
            x, y = make_samples()

            self.x = np.array(x)
            self.y = np.array(y)
        except Timeout.TimeoutException as ex:
            logger.error("Exceeded total timeout, not found solution")
            exit(-1)

    # uses curve_fit from scipy to evaluate coefficients of computational complexity function
    def test_complexity(self, fun, timeout):

        @Timeout(timeout)
        def test_complexity():
            coeff, err = curve_fit(fun, self.x, self.y)
            err = np.sqrt(np.diag(err))
            return coeff, err

        try:
            coefficients, err = test_complexity()
        except:
            logger.error("Found error while computing coefficients.")
            exit(-1)
        return coefficients, err

    # plot a function computation time graph
    def print(self):

        name = "O(" + self.complexity_name + ")"
        print("Estimated complexity = " + name, sep="")

        plt.plot(self.x, self.y, 'r-', label="samples")

        plt.plot(self.x, self.complexity_fun(self.x, *self.complexity_fun_coefficients), 'b-', label=name)
        plt.suptitle("Estimated complexity")
        plt.xlabel('N')
        plt.ylabel('time')
        plt.legend()
        plt.show()

    # returns maximum value of n for which function(n) takes less than max_time passed as argument
    def find_max_n(self, max_time):

        def binsearch(left, right):
            if left == right or left + 1 == right:
                return left
            center_result = self.complexity_fun((right + left) / 2, *self.complexity_fun_coefficients)
            if center_result > max_time:
                right = (right + left) / 2
            else:
                left = (right + left) / 2
            return binsearch(left, right)

        it = 1

        while self.complexity_fun(it, *self.complexity_fun_coefficients) < max_time:
            it *= 2
            if(it < 0):
                break

        if it < 0:
            logger.warning("Have not found interval.")
            return None
        return binsearch(it / 2, it)

    # returns estimated time of function(n) performance
    def get_estimated_time(self, n):
        return self.complexity_fun(n, *self.complexity_fun_coefficients)

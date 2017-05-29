from complexity.complexity_test import ComplexityTester

if __name__ == '__main__':

    firstly = """tab = [np.random.random() for i in range(1, n)]
kwargs['tab']=tab"""
    lastly = """"""

    def test1(n, **kwargs):
        sorted(kwargs['tab'])

    tester = ComplexityTester(firstly, lastly, test1)
    tester.print()
    print(tester.get_estimated_time(1000000))

    firstly = """tab = [[0]*n]*n
kwargs['tab']=tab"""

    def test2(n, **kwargs):
        for i in range(0, n - 1):
            for j in range(0, n - 1):
                kwargs['tab'][i][j] = 1

    tester = ComplexityTester(firstly, lastly, test2)
    tester.print()
    print(tester.get_estimated_time(1000000))

    firstly = """"""

    def test3(n):
        for i in range(1, 2**n):
            pass

    tester = ComplexityTester(firstly, lastly, test3)
    tester.print()
    print(tester.get_estimated_time(1000000))

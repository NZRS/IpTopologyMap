__author__ = 'secastro'

from multiprocessing import Pool
import os


def f(x):
    print "Doing work by ", os.getpid()
    return x*x

if __name__ == '__main__':
    pool = Pool(processes=4)
    result = pool.apply_async(f, [10])
    print result.get(timeout=1)
    print pool.map(f, range(20))

__author__ = 'labx'

import math, random, numpy

class RandomGenerator:
    def __init__(self, alpha, path, bins=1000):
        self.random_generator = random.Random()
        self.random_generator.seed()

        step = path/bins

        self.prefix = numpy.zeros(bins+1)
        self.points = numpy.zeros(bins+1)

        for index in range (0, bins+1):
            self.points[index] = index*step

            if index == 0:
                self.prefix[0] = self.getFrequency(alpha, 0)
            else:
                self.prefix[index] = self.prefix[index-1] + self.getFrequency(alpha, index*step)

    def random(self):
        n = len(self.prefix)
        r = (self.random_generator.random() * self.prefix[n-1]) + 1

        # Find index of ceiling of r in prefix array
        return self.points[self.findCeil(r, 0, n-1)]

    def getFrequency(self, alpha, x):
        return math.floor(10000*math.exp(-alpha*x))

    def findCeil(self, r, l, h):
        while (l < h):
            mid = l + ((h - l) >> 1)  #Same as mid = (l+h)/2

            if r > self.prefix[mid]:
                l = mid + 1
            else:
                h = mid

        if self.prefix[l] >= r:
            return l
        else:
            return -1

if __name__ == "__main__":

    random = RandomGenerator(264, 0.01)

    #for i in range(0, 1001):
    #    print(random.prefix[i])


    for i in range(0, 1000):
        print(random.random())
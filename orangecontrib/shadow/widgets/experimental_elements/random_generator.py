__author__ = 'labx'

import math, random, numpy

class AbstractRandom:
    def __init__(self, bins=1000):
        self.random_generator = random.Random()
        self.random_generator.seed()

        self.prefix = numpy.zeros(bins+1)
        self.points = numpy.zeros(bins+1)

    def random(self):
        n = len(self.prefix)
        r = (self.random_generator.random() * self.prefix[n-1]) + 1

        # Find index of ceiling of r in prefix array
        return self.points[self.findCeil(r, 0, n-1)]

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

class LorentzianRandom(AbstractRandom):
    def __init__(self, beta, bins=1000):
        super().__init__(bins=bins)

        fwhm = beta * (2 / numpy.pi)
        gamma = fwhm / 2

        step = 40*fwhm/bins

        for index in range (0, bins+1):
            x = -20*fwhm + index*step

            self.points[index] = x

            if index == 0:
                self.prefix[0] = self.getFrequency(gamma, x)
            else:
                self.prefix[index] = self.prefix[index-1] + self.getFrequency(gamma, x)

    def getFrequency(self, gamma, x):
        return 1 / ((numpy.pi*gamma)*(1 + (x/gamma)**2))


class AbsorptionRandom(AbstractRandom):
    def __init__(self, alpha, path, bins=1000):
        super().__init__(bins=bins)

        step = path/bins

        for index in range (0, bins+1):
            self.points[index] = index*step

            if index == 0:
                self.prefix[0] = self.getFrequency(alpha, 0)
            else:
                self.prefix[index] = self.prefix[index-1] + self.getFrequency(alpha, index*step)

    def getFrequency(self, alpha, x):
        return math.floor(10000*math.exp(-alpha*x))

import matplotlib.pyplot as plt

if __name__ == "__main__":

    random = AbsorptionRandom(264, 0.01)
    #random = LorentzianRandom(0.001)

    s = []

    for i in range(0, 1000000):
        s.append(random.random())

    plt.hist(s, bins=1000)
    plt.show()

#    s = numpy.random.standard_cauchy(100000000)
#    s = s[(s>-50) & (s<50)]  # truncate distribution so it plots well
#    plt.hist(s, bins=1000)
#    plt.show()
from collections import namedtuple
import numpy as np


Result = namedtuple("Result", ("rank", "index", "value"))


class SimilarityMatrixError(Exception):
    pass


class SimilarityMatrix(object):
    def __init__(self, items):
        try:
            self.n = len(items)
            self._items = list(items)
            self.matrix = np.empty((self.n, self.n), dtype=float)
            self._lookup = {}
            i = 0
            for item in items:
                self._lookup[item] = i
                i += 1
        except TypeError:
            raise SimilarityMatrixError("items should have a length and be iterable")

    def lookup_item(self, item):
        if item not in self._lookup.keys():
            raise SimilarityMatrixError("{} is not known in this matrix".format(item))
        return self._lookup[item]

    def lookup_index(self, n):
        if n >= self.n:
            raise SimilarityMatrixError("{} was out of range".format(n))
        return self._items[n]

    def put(self, item1, item2, value):
        i1 = self.lookup_item(item1)
        i2 = self.lookup_item(item2)
        self.put_index(i1, i2, value)

    def put_index(self, i1, i2, value):
        self.matrix[i1, i2] = value
        self.matrix[i2, i1] = value

    def get(self, item1, item2):
        i1 = self.lookup_item(item1)
        i2 = self.lookup_item(item2)
        return self.matrix[i1, i2]

    def get_ranked(self, item):
        i = self.lookup_item(item)
        return [i for i in self._ranked(i)]

    def ranked_matrix(self):
        # Not optimised (expensive!)
        m = SimilarityMatrix(self._items)
        for item1 in self._items:
            i1 = self.lookup_item(item1)
            for i2 in self._ranked(i1):
                m.put_index(i1, i2.index, i2.rank)
        return m

    def _ranked(self, i):
        indices = np.argsort(self.matrix[i, ])[::-1]  # type: np.ndarray
        j = 0
        for index in indices:
            rank = j
            value = self.lookup_index(index)
            yield Result(rank=rank, index=index, value=value)
            j += 1

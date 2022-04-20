import random as rd
from typing import List


class Distances:
    def __init__(self, dist: List[List[int]]):
        self.dist: List[List[int]] = dist

    def __str__(self):
        return '\n'.join(map(lambda x: ','.join(map(str,x)), self.dist))

    @staticmethod
    def new_dist() -> 'Distances':
        r = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
        for i in range(10):
            r[i - 1][i - 1] = 0
            for j in range(i, 10):
                if j >= len(r):
                    r.append([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                r[i][j] = rd.randint(1,10)
                r[j][i] = r[i][j]
        r[9][9] = 0
        return Distances(r)

    @staticmethod
    def get_from_string(src: str) -> 'Distances':
        return Distances(list(map(lambda x: list(map(int, x.split(','))), src.split('\n'))))
        
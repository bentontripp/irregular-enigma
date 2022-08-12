from sympy.utilities.iterables import multiset_permutations
import numpy as np

from jigsaw_board import *

class SudokuValues(JigsawSudoku):

    def __init__(self, size=9):
        # Maybe just try generating the puzzles WITH the values, and use that as an additional constraint? Or try generating values, shuffling, and creating regions when a 
        # possible solution is found?
        self.size = size
        # possible rows
        pr = self.perms()
        # start out with board that has unique rows/column values
        for i in range(0, self.size):
            if i == 0:
                m = pr.pop(0).reshape(1, self.size)
            else:
                m, pr = self.update_grid(m, pr) 
                

    def reshape_list_to_arr(self, perm):
        return np.reshape(np.array(perm), (1, self.size))

    def perms(self):
        p = [self.reshape_list_to_arr(perm) for perm in multiset_permutations(np.arange(1, self.size + 1))]
        np.random.shuffle(p)
        return p


    def update_grid(self, m, pr):
        for i in range(0, len(pr)):
            cm = np.concatenate((m, pr[i]), axis=0)
            if len([col for col in range(0, self.size) if np.unique(cm[:, col]).size == cm.shape[0]]) == self.size:
                pr.pop(i)
                return cm, pr
            else:
                pr.pop(i)

if __name__ == '__main__':
    grid = SudokuValues()
# import libraries
from sympy.utilities.iterables import multiset_permutations
import numpy as np
from random import choice

############################################################################################################################################
# SudokuValues Class

class SudokuValues:

    def __init__(self, size=9, set_to_default=False):
        self.size = size
        if set_to_default is True:
            self.grid = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9], 
                                  [4, 5, 6, 7, 8, 9, 1, 2, 3], 
                                  [7, 8, 9, 1, 2, 3, 4, 5, 6], 
                                  [2, 1, 4, 3, 6, 5, 8, 9, 7], 
                                  [3, 6, 5, 8, 9, 7, 2, 1, 4], 
                                  [8, 9, 7, 2, 1, 4, 3, 6, 5], 
                                  [5, 3, 1, 6, 4, 2, 9, 7, 8], 
                                  [6, 4, 2, 9, 7, 8, 5, 3, 1], 
                                  [9, 7, 8, 5, 3, 1, 6, 4, 2]])
        else:
            # possible rows
            pr = self.perms()
            # start out with board that has unique rows/column values
            for i in range(0, self.size):
                if i == 0:
                    m = pr.pop(0).reshape(1, self.size)
                else:
                    m, pr = self.update_grid(m, pr) 
            self.grid = m
                
    #----------------------------------------------------------------------------------------------------------------------------------------
    # Methods to generate basice board with unique rows/columns in `__init__()`

    # convert list to array, reshape to size (1, self.size) to be concatenated to m
    def reshape_list_to_arr(self, perm):
        return np.reshape(np.array(perm), (1, self.size))

    # generate all permutations of 1:self.size, reshape each perm; shuffle
    def perms(self):
        p = [self.reshape_list_to_arr(perm) for perm in multiset_permutations(np.arange(1, self.size + 1))]
        np.random.shuffle(p)
        return p

    # iteratively check if each permutation can be used as a new row; if not, remove; if yes, concatenate; return with reduced permutations
    def update_grid(self, m, pr):
        for i in range(0, len(pr)):
            cm = np.concatenate((m, pr[i]), axis=0)
            if len([col for col in range(0, self.size) if np.unique(cm[:, col]).size == cm.shape[0]]) == self.size:
                pr.pop(i)
                return cm, pr
            else:
                pr.pop(i)
    #----------------------------------------------------------------------------------------------------------------------------------------
    # Methods to divide up regions

    # select random corner to be the first region
    def random_corner(self):
        return choice([(0, 0), (0, self.size-1), (self.size-1, 0), (self.size-1, self.size-1)])
    
    # get all possible index combinations that might construct a region of size self.size
    def corner_ind(self):
        c_idx = self.random_corner()
        corner = self.grid[c_idx]
        print(corner)


if __name__ == '__main__':
    s = SudokuValues(size=9, set_to_default=True)
    print(s.grid)
    s.corner_ind()
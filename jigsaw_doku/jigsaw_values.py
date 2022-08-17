# import libraries
from sympy.utilities.iterables import multiset_permutations
import numpy as np
from random import choice
import time, logging, functools, operator, rasterio.features, shapely.geometry
from rich.logging import RichHandler
       
logger_blocklist=[
        "matplotlib",
        "fontTools",
        "shapely",
        "PIL",
        "itertools"]

# Set logging format
FORMAT = "%(message)s"
logging.basicConfig(
    level=20, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)  # set level=20 or logging.INFO to turn off debug. to not set, level = "NOTSET"
for module in logger_blocklist:
    logging.getLogger(module).setLevel(logging.WARNING)
logger = logging.getLogger("rich")


# globals
global PUZZLE_GEN_START_TIME, TIMEOUT
TIMEOUT = 2

############################################################################################################################################
# Helper functions

# Functions to generate triangular region indices available to each of the four corners
# Upper-left, Upper-right, Lower-left, Lower-right (ul, ur, ll, lr)
def gen_upper_left_y(size=9):
    out = list()
    for i in range(0, size):
        out += [i]*(size-i)
    return np.array(out)

def gen_upper_left_x(size=9):
    out = list()
    for i in range(0, size):
        out += list(np.arange(0, size-i))
    return np.array(out)

def gen_lower_right_y(size=9):
    out = list()
    for i in range(0, size):
        out += list(np.arange(i, size))
    return np.array(out)

def gen_lower_right_x(size=9):
    out = list()
    for i in range(0, size):
        out += [size-i-1]*(size-i)
    return np.array(out)

def gen_ul_indices(size=9):
    return [(y, x) for y, x in zip(gen_upper_left_y(size), gen_upper_left_x(size))]

def gen_ll_indices(size=9):
    return [(y, x) for y, x in zip(np.tril_indices(size)[0], np.tril_indices(size)[1])]

def gen_ur_indices(size=9):
    return [(y, x) for y, x in zip(np.triu_indices(size)[0], np.triu_indices(size)[1])]

def gen_lr_indices(size=9):
    return [(y, x) for y, x in zip(gen_lower_right_y(size), gen_lower_right_x(size))]

def get_adjacent(tri_ind):
    adjacent = dict()
    for idx in range(0, len(tri_ind)):
        i = tri_ind[idx]
        idx_list = tri_ind[:idx] + tri_ind[idx + 1:]
        adjacent.update({i: [j for j in idx_list \
            if (abs(j[0] - i[0]) == 1 and j[1] - i[1] == 0) \
                or (abs(j[1] - i[1]) == 1 and j[0] - i[0] == 0)]})
    return adjacent

# Flatten nested lists
def flatten(nl):
    return functools.reduce(operator.iconcat, nl, [])

############################################################################################################################################
# SudokuValues Class

class SudokuValues:

    def __init__(self, size=9, set_to_default=False, attempts_per_grid=1e6):
        self.size = size
        # Generate corner regions
        self.corners = None
        # init exclusions (edge rows/columns)
        self.exclude = [
            tuple((i, 0) for i in range(0, self.size)),
            tuple((0, i) for i in range(0, self.size)),
            tuple((i, self.size-1) for i in range(0, self.size)),
            tuple((0, i) for i in range(self.size-1, -1, -1)),
            tuple((i, 0) for i in range(self.size-1, -1, -1)),
            tuple((self.size-1, i) for i in range(0, self.size)),
            tuple((i, self.size-1) for i in range(self.size-1, -1, -1)),
            tuple((self.size-1, i) for i in range(self.size-1, -1, -1))
        ]
        if set_to_default is True:
            if self.size != 9:
                logger.info('Resetting size to default (9)')
                self.size = 9
            self.grid = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9], 
                                  [4, 5, 6, 7, 8, 9, 1, 2, 3], 
                                  [7, 8, 9, 1, 2, 3, 4, 5, 6], 
                                  [2, 1, 4, 3, 6, 5, 8, 9, 7], 
                                  [3, 6, 5, 8, 9, 7, 2, 1, 4], 
                                  [8, 9, 7, 2, 1, 4, 3, 6, 5], 
                                  [5, 3, 1, 6, 4, 2, 9, 7, 8], 
                                  [6, 4, 2, 9, 7, 8, 5, 3, 1], 
                                  [9, 7, 8, 5, 3, 1, 6, 4, 2]])
            # Generate corners
            self.corner_loop(attempts_per_grid)
        else:
            corners_complete = False
            while corners_complete is False:
                # possible rows
                pr = self.perms()
                # start out with board that has unique rows/column values
                for i in range(0, self.size):
                    if i == 0:
                        m = pr.pop(0).reshape(1, self.size)
                    else:
                        m, pr = self.update_grid(m, pr) 
                self.grid = m
                logger.info('Grid:\n{}'.format(self.grid))
                corners_complete = self.corner_loop(attempts_per_grid)

        
        
    # Loop to generate corners until success
    def corner_loop(self, attempts_per_grid):
        attempts = 0
        start_attempts = time.time()
        while True:
            attempts += 1
            try:
                self.corners = self.gen_corner_regions()
                logger.info('{} Attempts completed in {} seconds'.format(attempts, time.time() - start_attempts))
                return True
            except:
                if attempts >= attempts_per_grid:
                    logger.info('{} Attempts completed in {} seconds'.format(attempts, time.time() - start_attempts))
                    logger.info('No corner solutions found given the selected arrangement. Starting over...')
                    return False
        
        
                
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
            try:
                cm = np.concatenate((m, pr[i]), axis=0)
            except IndexError:
                logger.error('m: {}\n i: {}\n len(pr): {}\n rmv_idcs: {}'.format(m, i, len(pr), rmv_idcs))
                raise IndexError
            if len([col for col in range(0, self.size) if np.unique(cm[:, col]).size == cm.shape[0]]) == self.size:
                return cm, pr[i + 1:]
            else:
                continue
    #----------------------------------------------------------------------------------------------------------------------------------------
    # Methods to divide up regions

    # select random corner to be the first region
    def random_corner(self, exclude_corners=list()):
        return choice([c for c in [(0, 0), (0, self.size-1), (self.size-1, 0), (self.size-1, self.size-1)] \
            if c not in exclude_corners]), exclude_corners
    
    # test for any blocked regions that are too small
    def test_for_blocked(self, region_i):
        x = self.grid
        # mask region_i
        for i in region_i:
            x[i] = -1
        polygons = [shapely.geometry.Polygon(shape[0]["coordinates"][0]) \
            for shape in rasterio.features.shapes((x == -1) + 0)]
        for p in polygons:
            if p.area % self.size != 0:
                return True

    # Recursively generate the corner regions
    def gen_corner_regions(self, completed_corners=list(), exclude_corners=list()):
        n_regions = len(completed_corners)
        if n_regions > 0:
            all_completed = flatten(completed_corners)
            exclude_corners = list(set(exclude_corners + all_completed))
        else:
            all_completed = list()
        # start w/ random corner
        try:
            corner, exclude_corners = self.random_corner(exclude_corners=exclude_corners)
        except (TypeError, IndexError):
            raise Exception('There are no possible corners that work given this arrangement')
        # pick a random direction to start, generate available indices and their adjacent indices
        if corner == (0, 0):
            start_1 = (1, 0)
            start_2 = (0, 1)
            adj = get_adjacent(gen_ul_indices(self.size))
            for k in adj.keys():
                adj[k] = [v for v in adj[k] if v not in all_completed]
            # column = tuple((i, 0) for i in range(0, self.size))
            # row = tuple((0, i) for i in range(0, self.size))
        elif corner == (0, self.size-1):
            start_1 = (1, self.size-1)
            start_2 = (0, self.size-2)
            adj = get_adjacent(gen_ur_indices(self.size))
            for k in adj.keys():
                adj[k] = [v for v in adj[k] if v not in all_completed]
            # column = tuple((i, self.size-1) for i in range(0, self.size))
            # row = tuple((0, i) for i in range(self.size-1, -1, -1))
        elif corner == (self.size-1, 0):
            start_1 = (self.size-2, 0)
            start_2 = (self.size-1, 1)
            adj = get_adjacent(gen_ll_indices(self.size))
            for k in adj.keys():
                adj[k] = [v for v in adj[k] if v not in all_completed]
            # column = tuple((i, 0) for i in range(self.size-1, -1, -1))
            # row = tuple((self.size-1, i) for i in range(0, self.size))
        else:
            start_1 = (self.size-2, self.size-1)
            start_2 = (self.size-1, self.size-2)
            adj = get_adjacent(gen_lr_indices(self.size))
            for k in adj.keys():
                adj[k] = [v for v in adj[k] if v not in all_completed]
            # column = tuple((i, self.size-1) for i in range(self.size-1, -1, -1))
            # row = tuple((self.size-1, i) for i in range(self.size-1, -1, -1))
        # random starting checks
        start_choices = [sc for sc in [start_1, start_2] if sc not in all_completed]
        if len(start_choices) > 1:
            start = choice(start_choices)
            start_choices = [choice for choice in start_choices if choice != start]
        elif len(start_choices) == 1:
            start = start_choices[0]
            start_choices = []
        else:
            # TODO
            raise Exception('No possible solution given the current arrangement')
        # start != corner, so move on 
        # start building region (of indices, and of values)
        region_i = [corner, start]
        region_v = [self.grid[corner], self.grid[start]]
        next = 2
        PUZZLE_GEN_START_TIME = time.time()
        while next < self.size:
            # get adjacent
            next_ind = [i for i in adj[region_i[next - 1]] if i not in region_i \
                and self.grid[i] not in region_v and tuple(region_i + [i]) not in self.exclude]
            if len(next_ind) == 0:
                if len(region_i) > 2:
                    if time.time() - PUZZLE_GEN_START_TIME >= TIMEOUT:
                        raise TimeoutError
                    self.exclude.append(tuple(region_i))
                    region_i.pop(-1)
                    region_v.pop(-1)
                elif len(region_i) == 2 and len(start_choices) == 1:
                    if time.time() - PUZZLE_GEN_START_TIME >= TIMEOUT:
                        raise TimeoutError
                    self.exclude.append(tuple(region_i))
                    start = start_choices.pop(0)
                    region_i = [corner, start]
                    region_v = [self.grid[corner], self.grid[start]]
                else:
                    exclude_corners.append(corner)
                    return self.gen_corner_regions(exclude_corners=exclude_corners)
            else:
                next_ind = choice(next_ind)
                region_i.append(next_ind)
                region_v.append(self.grid[next_ind])
            # make sure none are blocked
            if len(region_i) == self.size:
                if self.test_for_blocked(region_i):
                    self.exclude.append(tuple(region_i))
                    region_i.pop(-1)
                    region_v.pop(-1)
            next = len(region_i)
        logger.info('CORNER-REGION {}\nStarting Indices: {}\nStarting Region Values: {}'\
            .format(n_regions+1, region_i, region_v))
        completed_corners.append(region_i)
        if len(completed_corners) == 4:
            return completed_corners
        else:
            return self.gen_corner_regions(completed_corners, exclude_corners) 

if __name__ == '__main__':
    s = SudokuValues(size=9, set_to_default=False)
    print(s.corners)
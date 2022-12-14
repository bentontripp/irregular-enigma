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


global PUZZLE_GEN_START_TIME, TIMEOUT
TIMEOUT = 2



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


def random_corner(size, exclude_corners=list()):
    return choice([c for c in [(0, 0), (0, size-1), (size-1, 0), (size-1, size-1)] \
        if c not in exclude_corners]), exclude_corners
    

def get_adjacent(tri_ind):
    adjacent = dict()
    for idx in range(0, len(tri_ind)):
        i = tri_ind[idx]
        idx_list = tri_ind[:idx] + tri_ind[idx + 1:]
        adjacent.update({i: [j for j in idx_list \
            if (abs(j[0] - i[0]) == 1 and j[1] - i[1] == 0) \
                or (abs(j[1] - i[1]) == 1 and j[0] - i[0] == 0)]})
    return adjacent

def test_for_blocked(x, region_i, size):
    # mask region_i
    for i in region_i:
        x[i] = -1
    polygons = [shapely.geometry.Polygon(shape[0]["coordinates"][0]) \
        for shape in rasterio.features.shapes((x == -1) + 0)]
    for p in polygons:
        if p.area % size != 0:
            return True

# Flatten nested lists
def flatten(nl):
    return functools.reduce(operator.iconcat, nl, [])

def gen_corner_regions(x, size, completed_corners=list(), exclude_corners=list()):
    n_regions = len(completed_corners)
    if n_regions > 0:
        all_completed = flatten(completed_corners)
        exclude_corners += all_completed
    else:
        all_completed = []
    # start w/ random corner
    try:
        corner, exclude_corners = random_corner(size, exclude_corners=exclude_corners)
    except (TypeError, IndexError):
        Exception('There are no possible corners that work given this arrangement')
    # pick a random direction to start, generate available indices and their adjacent indices
    if corner == (0, 0):
        # logger.info('Starting corner is UL')
        start_1 = (1, 0)
        start_2 = (0, 1)
        adj = get_adjacent(gen_ul_indices(size))
        for k in adj.keys():
            adj[k] = [v for v in adj[k] if v not in all_completed]
        column = tuple((i, 0) for i in range(0, size))
        row = tuple((0, i) for i in range(0, size))
    elif corner == (0, size-1):
        # logger.info('Starting corner is UR')
        start_1 = (1, size-1)
        start_2 = (0, size-2)
        adj = get_adjacent(gen_ur_indices(size))
        for k in adj.keys():
            adj[k] = [v for v in adj[k] if v not in all_completed]
        column = tuple((i, size-1) for i in range(0, size))
        row = tuple((0, i) for i in range(size-1, -1, -1))
    elif corner == (size-1, 0):
        # logger.info('Starting corner is LL')
        start_1 = (size-2, 0)
        start_2 = (size-1, 1)
        adj = get_adjacent(gen_ll_indices(size))
        for k in adj.keys():
            adj[k] = [v for v in adj[k] if v not in all_completed]
        column = tuple((i, 0) for i in range(size-1, -1, -1))
        row = tuple((size-1, i) for i in range(0, size))
    else:
        # logger.info('Starting corner is LR')
        start_1 = (size-2, size-1)
        start_2 = (size-1, size-2)
        adj = get_adjacent(gen_lr_indices(size))
        for k in adj.keys():
            adj[k] = [v for v in adj[k] if v not in all_completed]
        column = tuple((i, size-1) for i in range(size-1, -1, -1))
        row = tuple((size-1, i) for i in range(size-1, -1, -1))
    # start out excluding row & column (and any existing regions)
    exclude = [row, column]
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
    region_v = [x[corner], x[start]]
    next = 2
    PUZZLE_GEN_START_TIME = time.time()
    while next < size:
        # get adjacent
        next_ind = [i for i in adj[region_i[next - 1]] if i not in region_i \
            and x[i] not in region_v and tuple(region_i + [i]) not in exclude]
        if len(next_ind) == 0:
            if len(region_i) > 2:
                if time.time() - PUZZLE_GEN_START_TIME >= TIMEOUT:
                    raise TimeoutError
                exclude.append(tuple(region_i))
                region_i.pop(-1)
                region_v.pop(-1)
            elif len(region_i) == 2 and len(start_choices) == 1:
                if time.time() - PUZZLE_GEN_START_TIME >= TIMEOUT:
                    raise TimeoutError
                logger.info('RESETTING START CHOICE:\nregion_i: {};\nregion_v: {};'.format(region_i, region_v))
                exclude.append(tuple(region_i))
                start = start_choices.pop(0)
                region_i = [corner, start]
                region_v = [x[corner], x[start]]
            else:
                exclude_corners.append(corner)
                logger.info('EXCLUDING CORNER(S): {};'.format(exclude_corners))
                return gen_random_region(x, size, exclude_corners=exclude_corners)
        else:
            next_ind = choice(next_ind)
            region_i.append(next_ind)
            region_v.append(x[next_ind])
        # make sure none are blocked
        if len(region_i) == size:
            if test_for_blocked(x, region_i, size):
                logger.info('TOO SMALL OF A SUB-REGION CREATED:\nregion_i: {};'.format(region_i))
                exclude.append(tuple(region_i))
                region_i.pop(-1)
                region_v.pop(-1)
        next = len(region_i)
    logger.info('CORNER-REGION {}\nStarting Indices: {}\nStarting Region Values: {}'\
        .format(n_regions+1, region_i, region_v))
    completed_corners.append(region_i)
    if len(completed_corners) == 4:
        logger.info('COMPLETE: {}'.format(completed_corners))
        return completed_corners
    else:
       return gen_corner_regions(x, size, completed_corners, exclude_corners) 

if __name__ == '__main__':
    size = 9
    x = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9], 
                [4, 5, 6, 7, 8, 9, 1, 2, 3], 
                [7, 8, 9, 1, 2, 3, 4, 5, 6], 
                [2, 1, 4, 3, 6, 5, 8, 9, 7], 
                [3, 6, 5, 8, 9, 7, 2, 1, 4],
                [8, 9, 7, 2, 1, 4, 3, 6, 5], 
                [5, 3, 1, 6, 4, 2, 9, 7, 8],
                [6, 4, 2, 9, 7, 8, 5, 3, 1], 
                [9, 7, 8, 5, 3, 1, 6, 4, 2]])
    print(x)
    corners = gen_random_region(x, size)
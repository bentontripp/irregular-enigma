import logging
from rich.logging import RichHandler
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
       
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


def row_to_cell(row, r, cells, x_dir, y_dir):
    xs = (row[0], row[0] + x_dir)
    ys = (row[1], row[1] + y_dir)
    cell = box(min(xs), min(ys), max(xs), max(ys))
    if Point(row[0] + x_dir/2, row[1] + y_dir/2).within(r) and not Point(row[0] + x_dir/2, row[1] + y_dir/2).within(unary_union(cells)):
        cells.append(cell)
    return cells


def region_exterior_cells(r):
    crds = list(r.exterior.coords)
    cells = list()
    for i in range(1, len(crds)):
        row = crds[i]
        if row[0] != crds[i - 1][0]:
            # move in x direction
            x_mv = row[0] - crds[i - 1][0]
            if x_mv == 1:
                cells = row_to_cell(row, r, cells, x_dir=-1, y_dir=-1)
            else:
                cells = row_to_cell(row, r, cells, x_dir=1, y_dir=1)
        else:
            # move in y direction
            y_mv = row[1] - crds[i - 1][1]
            if y_mv == 1:
                cells = row_to_cell(row, r, cells, x_dir=1, y_dir=-1)
            else:
                cells = row_to_cell(row, r, cells, x_dir=-1, y_dir=1)
    return cells


def divide_region(r):
    ext_cells = region_exterior_cells(r)
    int_cells = r.difference(unary_union(ext_cells))
    if type(int_cells) == Polygon:
        crds = list(int_cells.exterior.coords)
        if len(crds) != 0:
            ext_cells += region_exterior_cells(int_cells)
    else:
        crds = list()
        for part in int_cells.geoms:
            ext_cells += region_exterior_cells(part)
    return ext_cells


# Adjust starting point along exterior as needed
def check_point(point, available_region, ext=True):
    cell = box(point[0], point[1], point[0]+1, point[1]+1)
    if Point(point[0]+.5, point[1]+.5).within(available_region):
        return cell
    else:
        if ext is True:
            for xy in (0, 1):
                if point[xy] == 0:
                    if Point(point[0]+.5, point[1]-.5).within(available_region) and xy == 0:
                        return box(point[0], point[1]-1, point[0]+1, point[1])
                    elif Point(point[0]-.5, point[1]+.5).within(available_region) and xy == 1:
                        return box(point[0]-1, point[1], point[0], point[1]+1)
        else:
            if Point(point[0]+.5, point[1]-.5).within(available_region):
                return box(point[0], point[1]-1, point[0]+1, point[1])
            elif Point(point[0]-.5, point[1]+.5).within(available_region):
                return box(point[0]-1, point[1], point[0], point[1]+1)
            elif Point(point[0]-.5, point[1]-.5).within(available_region):
                return box(point[0]-1, point[1]-1, point[0], point[1])
    raise ValueError
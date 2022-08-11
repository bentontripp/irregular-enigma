import random
from functools import reduce

from jigsaw_board import *
from utils import *

class SudokuValues(JigsawSudoku):

    def __init__(self):
        # Maybe just try generating the puzzles WITH the values, and use that as an additional constraint? Or try generating values, shuffling, and creating regions when a 
        # possible solution is found?
        pass
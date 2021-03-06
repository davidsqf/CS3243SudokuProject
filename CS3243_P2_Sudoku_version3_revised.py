import sys
import copy
import time

# Running script: given code can be run with the command:
# python file.py, ./path/to/init_state.txt ./output/output.txt

def setCopy(values):
    set_copy = set()
    for value in values:
        set_copy.add(value)
    return set_copy

def puzzleCopy(puzzle):
    puzzle_copy = [[puzzle[i][j] for j in xrange(9)]for i in xrange(9)]
    return puzzle_copy

class Cell:
    def __init__(self, value):
        self.value = value
        self.domain = set()
        self.neighbors = set()

    def __str__(self):
        return str(self.value)

class SudokuPuzzle:
    def __init__(self,matrix,row_constraints,col_constraints,box_constraints):
        self.matrix = matrix
        self.row_constraints = row_constraints
        self.col_constraints = col_constraints
        self.box_constraints = box_constraints
        self.initialize_domains()
        self.initialize_neighbors()
        self.count = 0

    def __hash__(self):
        return hash(str(self.matrix))

    def __str__(self):
        out = ""
        for row in range(9):
            for col in range(9):
                out = out + " " + str(self.matrix[row][col])
            out = out + "\n"
        return out

    #initialize the domain of each cell inside the Sudoku puzzle
    def initialize_domains(self):
        for row in range(9):
            for col in range(9):
                domain = self.row_constraints[row].intersection(self.col_constraints[col],
                                                                self.box_constraints[row//3][col//3])
                self.matrix[row][col].domain = domain

    # initialize the neighbors of each cell inside the Sudoku puzzle
    def initialize_neighbors(self):
        for row in range(9):
            for col in range(9):
                self.matrix[row][col].neighbors = self.find_neighbors(row, col)

    # find all unassigned neighbor cells of the cell at coordinate (row, col)
    def find_neighbors(self, row, col):
        neighbors = set()
        for i in range(9):
            if i != row and self.matrix[i][col].value == 0:
                neighbors.add((i, col))
            if i != col and self.matrix[row][i].value == 0:
                neighbors.add((row, i))
        box_row = row // 3 * 3
        box_col = col // 3 * 3
        for i in range(box_row, box_row + 3):
            for j in range(box_col, box_col + 3):
                if i != row and j != col and self.matrix[i][j].value == 0:
                    neighbors.add((i, j))
        return neighbors

    #choose the coordinate of the next cell to be assigned
    #heuristcs implemented: Most Constrained Variable
    def choose_cell_to_assign(self):
        min_domain = 100
        chosen_row = None
        chosen_col = None
        for row in range(9):
            for col in range(9):
                value = self.matrix[row][col].value
                if value == 0:
                    if len(self.matrix[row][col].domain) < min_domain:
                        min_domain = len(self.matrix[row][col].domain)
                        chosen_row = row
                        chosen_col = col
        return (chosen_row, chosen_col)

    #arrange the values of a cell's domain for later assignment
    #heuristics implemented: Least Constraining Value
    def arrange_value_to_assign(self, row, col):
        value_and_conflict_table = set()
        for value in self.matrix[row][col].domain:
            no_of_conflict = self.count_conflict(row, col, value)
            value_and_conflict_table.add((value, no_of_conflict))
        sorted(value_and_conflict_table, key=lambda x: x[1], reverse=True)
        return value_and_conflict_table

    #count the number of conflict that would be caused if a value is assigned at coordinate (row, col)
    def count_conflict(self, row, col, value):
        no_of_conflict = 0
        for (i, j) in self.matrix[row][col].neighbors:
            if value in self.matrix[i][j].domain:
                no_of_conflict += 1
        return no_of_conflict

    #assign a value to a cell and update domains and constraints
    def assign(self, row, col, new_value):
        self.matrix[row][col].value = new_value
        self.row_constraints[row].remove(new_value)
        self.col_constraints[col].remove(new_value)
        self.box_constraints[row // 3][col // 3].remove(new_value)

        for i, j in self.matrix[row][col].neighbors:
            self.matrix[i][j].neighbors.remove((row, col))

        self.initialize_domains()

    #unassign a value from a cell and update domains and constraints
    def undo_assign(self, row, col, new_value):
        self.matrix[row][col].value = 0
        self.row_constraints[row].add(new_value)
        self.col_constraints[col].add(new_value)
        self.box_constraints[row // 3][col // 3].add(new_value)

        for i, j in self.matrix[row][col].neighbors:
            self.matrix[i][j].neighbors.add((row, col))

        self.initialize_domains()

    #check if the value assignment at coordinate (row,col) is valid
    def is_valid(self):
        for i in range(9):
            for j in range(9):
                if self.matrix[i][j].value == 0 and len(self.matrix[i][j].domain) == 0:
                    return False
        return True

    def backtrack_search(self):
        self.count += 1
        if self.is_answer():
            return True
        if not self.is_valid():
            return False
        (row, col) = self.choose_cell_to_assign()
        domain_copy = self.arrange_value_to_assign(row, col)
        for new_value, no_conflict in domain_copy:
            self.assign(row, col, new_value)
            result = self.backtrack_search()
            if result is True:
                return True
            else:
                self.undo_assign(row, col, new_value)

    def is_answer(self):
        for row in range(9):
            for col in range(9):
                if self.matrix[row][col].value == 0:
                    return False
        return True

class Sudoku(object):
    def __init__(self, puzzle):
        # you may add more attributes if you need
        self.puzzle = puzzle # self.puzzle is a list of lists
        self.ans = puzzleCopy(puzzle) # self.ans is a list of lists

        self.matrix = self.initialize_cells(self.puzzle)

        self.row_constraints = [set([1, 2, 3, 4, 5, 6, 7, 8, 9]) for i in range(9)] #set of values that haven't appeared in each row
        self.col_constraints = [set([1, 2, 3, 4, 5, 6, 7, 8, 9]) for i in range(9)] #set of values that haven't appeared in each collumn
        self.box_constraints = [[set([1, 2, 3, 4, 5, 6, 7, 8, 9]) for i in range(3)] for j in range(3)] #set of values that haven't appeared in each 3x3 box
        
        self.initialize_constraints()

    #initialize the value inside each cell with given input
    def initialize_cells(self,puzzle):
        matrix = [[Cell(0) for i in range(9)] for j in range(9)]
        for row in range(9):
            for col in range(9):
                matrix[row][col].value = puzzle[row][col]
        return matrix

    #initialize the row, collumn, and 3x3 box constraints of the Sudoku puzzle
    def initialize_constraints(self):
        for row in range(9):
            for col in range(9):
                value = self.matrix[row][col].value
                if value != 0:
                    self.row_constraints[row].remove(value)
                    self.col_constraints[col].remove(value)
                    self.box_constraints[row//3][col//3].remove(value)

    # def generate_domains

    def solve(self):
        # TODO: Write your code here
        start_time = time.time()
        sudokuPuzzle = SudokuPuzzle(self.matrix, self.row_constraints, self.col_constraints, self.box_constraints)
        sudokuPuzzle.backtrack_search()
        end_time = time.time()
        print("Version: BackTracking Search + Minimum Remaining Values + Most Constraining Value Heuristics")
        print("Time elapsed " + str(end_time - start_time))
        print("Number of states traversed: " + str(sudokuPuzzle.count))
        return sudokuPuzzle.matrix

    # you may add more classes/functions if you think is useful
    # However, ensure all the classes/functions are in this file ONLY
    # Note that our evaluation scripts only call the solve method.
    # Any other methods that you write should be used within the solve() method.

if __name__ == "__main__":
    # STRICTLY do NOT modify the code in the main function here
    if len(sys.argv) != 3:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise ValueError("Wrong number of arguments!")

    try:
        f = open(sys.argv[1], 'r')
    except IOError:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise IOError("Input file not found!")

    puzzle = [[0 for i in range(9)] for j in range(9)]
    lines = f.readlines()

    i, j = 0, 0
    for line in lines:
        for number in line:
            if '0' <= number <= '9':
                puzzle[i][j] = int(number)
                j += 1
                if j == 9:
                    i += 1
                    j = 0

    sudoku = Sudoku(puzzle)
    ans = sudoku.solve()

    with open(sys.argv[2], 'a') as f:
        for i in range(9):
            for j in range(9):
                f.write(str(ans[i][j]) + " ")
            f.write("\n")

from pysat.solvers import Glucose3
from itertools import combinations
import os
import time

class GemHunterSolver:
    def __init__(self, grid):
        self.grid = grid
        self.nrows = len(grid)
        self.ncols = len(grid[0])
        self.clauses = [] 
        self.variable = {}
        self.trap_goal_cells = [] # Chứa các ô '_' cần xác định
        self.get_variable_index()
        self.generate_CNF()
        
    def get_variable_index(self):
        id = 1    
        for i in range (self.nrows):
            for j in range (self.ncols):
                if self.grid[i][j] == '_':
                    self.variable[(i, j)] = id
                    self.trap_goal_cells.append((i, j))
                    id += 1

    def get_neighbors(self, row, col):
        neighbors = []
        for i in [-1, 0 , 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0):
                    continue
                else:
                    newi = row + i
                    newj = col + j
                    if (0 <= newi < self.nrows and 0 <= newj < self.ncols):
                        if self.grid[newi][newj] == '_':
                            neighbors.append((newi, newj))
        return neighbors
    
    def generate_k(self, k, neighbors_var_index):
        n = len(neighbors_var_index)
        if n == 0:
            if k == 0:
                return [] 
            else:
                return None
        clauses = []
        if 0 <= k <= n:
            for sub in combinations(neighbors_var_index, n - k + 1):
                tmp = []
                for cell in sub:
                    tmp.append(self.variable[cell])
                clauses.append(tmp)
            for sub in combinations(neighbors_var_index, k + 1):
                tmp = []
                for cell in sub:
                    tmp.append(-self.variable[cell])
                clauses.append(tmp)
        return clauses

    def generate_CNF(self):
        for i in range (self.nrows):
            for j in range (self.ncols):
                if self.grid[i][j].isdigit():
                    neighbors = []
                    neighbors = self.get_neighbors(i, j)
                    k = int(self.grid[i][j])
                    clause = self.generate_k(k, neighbors)
                    self.clauses.extend(clause)
        unique_clauses = []
        visited = set()
        for clause in self.clauses:
            clause_tuple = tuple(sorted(clause))
            if clause_tuple not in visited:
                visited.add(clause_tuple)
                unique_clauses.append(clause)
        self.clauses = unique_clauses
    
    def solve(self):
        solver = Glucose3()
        for clause in self.clauses:
            solver.add_clause(clause)
        sat = solver.solve()
        if sat:
            model = solver.get_model()
            solution = {}
            for cell in self.trap_goal_cells:
                var = self.variable[cell]
                if var in model:
                    solution[cell] = 'T'
                else:
                    solution[cell] = 'G'
            return solution
        else:
            return None

    def brute_force_solve(self):
        start = time.time()
        from itertools import product
        variables = list(self.variable.values())
        cells = list(self.variable.keys())
        n = len(variables)
        for bits in product([False, True], repeat=n):
            if time.time() - start >= 100:
                return None
            assignment = {variables[i]: bits[i] for i in range(n)}
            if self.check_assignment(assignment):
                solution = {}
                for idx, cell in enumerate(cells):
                    solution[cell] = 'T' if bits[idx] else 'G'
                return solution
        return None

    def check_assignment(self, assignment):
        for clause in self.clauses:
            clause_satisfied = False
            for lit in clause:
                var = abs(lit)
                value = assignment.get(var, None)
                if value is None:
                    continue
                if lit > 0 and value:
                    clause_satisfied = True
                    break
                if lit < 0 and not value:
                    clause_satisfied = True
                    break
            if not clause_satisfied:
                return False
        return True

    def backtracking_solve(self):
        variables = list(self.variable.values())  # Danh sách các biến (ID)
        assignment = {}
        solution = self.backtrack(assignment, variables)
        if solution is None:
            return None
        # Chuyển đổi assignment thành dạng (i,j): 'T'/'G'
        result = {}
        for (i, j), var_id in self.variable.items():
            result[(i, j)] = 'T' if solution.get(var_id, False) else 'G'
        return result

    def backtrack(self, assignment, variables):
        if len(assignment) == len(variables):
            return assignment.copy()
        
        var = self.select_unassigned_variable(variables, assignment)
        for value in [False, True]:  # True: Trap, False: Gem
            assignment[var] = value
            if self.is_consistent(assignment):
                result = self.backtrack(assignment, variables)
                if result is not None:
                    return result
            del assignment[var]
        return None

    def select_unassigned_variable(self, variables, assignment):
        # Chọn biến chưa được gán đầu tiên
        for var in variables:
            if var not in assignment:
                return var
        return None

    def is_consistent(self, assignment):
        for clause in self.clauses:
            clause_possible = False  # Có khả năng clause được thỏa mãn trong tương lai?
            all_assigned = True      # Tất cả biến trong clause đã được gán?
            for lit in clause:
                var = abs(lit)
                if var not in assignment:
                    all_assigned = False
                    continue  # Biến chưa gán → clause có thể còn thỏa mãn sau này
                
                # Kiểm tra literal
                if (lit > 0 and assignment[var]) or (lit < 0 and not assignment[var]):
                    clause_possible = True
                    break
            
            # Nếu tất cả biến đã gán và không có literal nào thỏa → clause không thỏa
            if all_assigned and not clause_possible:
                return False
            # Nếu còn biến chưa gán → clause có thể thỏa trong tương lai → tạm chấp nhận
        return True

    def get_output_grid(self, solution):
        output = []
        for i in range(self.nrows):
            row = []
            for j in range(self.ncols):
                if self.grid[i][j] == '_':
                    row.append(solution.get((i, j), 'G'))
                else:
                    row.append(self.grid[i][j])
            output.append(', '.join(row))
        return '\n'.join(output)
    
                
def read_input(file_path):
    with open(file_path, 'r') as f:
        return [ [x.strip() for x in line.strip().split(',')] for line in f ]


def write_output(file_path, output, mode='a'):
    with open(file_path, mode) as f:
        f.write(output + "\n")



def main():
    input_folder = 'testcases'
    output_folder = 'testcases'
    
    x = input("Running input_x.txt, x: ")
    try:
        x = int(x)
    except ValueError:
        print("Please enter a valid integer!")
        return

    input_file = f'input_{x}.txt'
    output_file = os.path.join(output_folder, f'output_{x}.txt')
    input_path = os.path.join(input_folder, input_file)

    grid_data = read_input(input_path)
    grid = GemHunterSolver(grid_data)
    
    open(output_file, 'w').close()  

    start = time.perf_counter()
    solution_CNF = grid.solve()
    pysat_time = time.perf_counter() - start

    if solution_CNF:
        output_CNF = grid.get_output_grid(solution_CNF)
        print(f"PySAT solved input_{x} in {pysat_time:.8f} seconds")
        file_cnf = "PYSAT:\n" + output_CNF + "\n"
    else:
        print(f"No solution found for input_{x}")
        file_cnf = "PYSAT:\n" + "No solution found" + "\n"
    write_output(output_file, file_cnf)


    start = time.time()
    solution_bf = grid.brute_force_solve()
    bf_time = time.time() - start
    if solution_bf:
        output_brute = grid.get_output_grid(solution_bf)
        print(f"Brute-force solved input_{x} in {bf_time:.4f} seconds")
        file_brute = (
            "BRUTEFORCE:\n" + output_brute + "\n"
        )
        
    else:
        print("Brute-force found no solution")    
        file_brute = (
            "BRUTEFORCE:\n" + "No solution found" + "\n"
        )
    write_output(output_file, file_brute)

    start = time.perf_counter()
    solution_bt = grid.backtracking_solve()
    bt_time = time.perf_counter() - start
    if solution_bt:
        output_back = grid.get_output_grid(solution_bt)
        print(f"Backtracking solved input_{x} in {bt_time:.8f} seconds")
        file_bt = (
            "BACKTRACK:\n" + output_back + "\n"
        )
    else:
        print("Backtracking found no solution")
        file_bt = (
            "BACKTRACK:\n" + "No solution found" + "\n"
        )        
    write_output(output_file, file_bt)

if __name__ == "__main__":
    main()    


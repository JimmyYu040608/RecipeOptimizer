from src.recipe import Product
from src.shared_setup import create_demo_problem
from src.solver import ProductionProblem

OUTPUT_DIR = './images/demo'

def alternate_example_opt(save_path, title, obj_method='produce'):
    
    # Execute the program
    problem = create_demo_problem(obj_method)
    problem.optimize()
    problem.print_graph()
    problem.visualize_graph(save_path, title)

def demo():
    alternate_example_opt(f'{OUTPUT_DIR}/alternate_example_opt', 'Example [Opt]')

if __name__ == '__main__':
    demo()
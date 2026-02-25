# Scalarization: Weighted Sum Method
from src.recipe import Product
from src.shared_setup import create_demo_problem
from src.solver import ProductionProblem

OUTPUT_DIR = './images/moo'

def main():
    save_path = f'{OUTPUT_DIR}/value_waste_example'
    title = 'Value-Waste Tradeoff'
    
    problem = create_demo_problem('multi_obj_value_waste')
    problem.optimize()
    problem.create_graph()
    problem.visualize_graph(save_path, title)

if __name__ == '__main__':
    main()
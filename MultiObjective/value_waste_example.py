# Scalarization: Weighted Sum Method
from src.common import ObjMethods
from src.shared_setup import create_demo_problem

OUTPUT_DIR = './images/moo'

def main():
    save_path = f'{OUTPUT_DIR}/value_waste_example'
    title = 'Value-Waste Tradeoff'
    
    problem = create_demo_problem(ObjMethods.M_VALIE_WASTE)
    problem.optimize()
    problem.visualize_graph(save_path, title)

if __name__ == '__main__':
    main()
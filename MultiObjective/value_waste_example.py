# Scalarization: Weighted Sum Method
from src.utils import ObjMethods
from src.demo_data import DemoProblems

OUTPUT_DIR = './images/moo'

def main():
    save_path = f'{OUTPUT_DIR}/value_waste_example'
    title = 'Value-Waste Tradeoff'
    
    problem = DemoProblems.demo_example(ObjMethods.M_VALUE_WASTE)
    problem.optimize()
    problem.create_graph()
    problem.visualize_graph(save_path, title)

if __name__ == '__main__':
    main()
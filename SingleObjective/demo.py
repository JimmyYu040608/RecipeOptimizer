from src.demo_data import DemoProblems
from src.common import ObjMethods

OUTPUT_DIR = './images/demo'

def alternate_example_opt(save_path, title):
    
    # Execute the program
    problem = DemoProblems.demo_example(ObjMethods.S_VALUE)
    problem.optimize()
    problem.create_graph()
    problem.print_graph()
    problem.visualize_graph(save_path, title)

def demo():
    alternate_example_opt(f'{OUTPUT_DIR}/demo', 'Example [Opt]')

if __name__ == '__main__':
    demo()
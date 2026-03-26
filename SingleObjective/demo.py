from src.shared_setup import create_demo_problem

OUTPUT_DIR = './images/demo'

def alternate_example_opt(save_path, title):
    
    # Execute the program
    problem = create_demo_problem()
    problem.optimize()
    problem.create_graph()
    problem.print_graph()
    problem.visualize_graph(save_path, title)

def demo():
    alternate_example_opt(f'{OUTPUT_DIR}/demo', 'Example [Opt]')

if __name__ == '__main__':
    demo()
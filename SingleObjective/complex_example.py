import os
from src.demo_data import DemoProblems
from src.utils import ObjMethods

OUTPUT_DIR = "./images/soo"

def run_complex_example_1():
    problem_produce = DemoProblems.complex_example(ObjMethods.S_VALUE)
    problem_waste = DemoProblems.complex_example(ObjMethods.S_WASTE)
    problem_PnW = DemoProblems.complex_example(ObjMethods.S_VALUE_WASTE)
        
    if not problem_produce.validate():
        print("Problem (Produce) is invalid")
        return
    if not problem_waste.validate():
        print("Problem (Waste) is invalid")
        return
    if not problem_PnW.validate():
        print("Problem (Produce and Waste) is invalid")
        return
    
    # Create output_png folder if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Heuristics of maximizing target production
    save_path = f'{OUTPUT_DIR}/complex_graph_1_value'
    problem_produce.optimize()
    problem_produce.create_graph()
    # problem_produce.print_graph()
    problem_produce.visualize_graph(save_path, 'Complex Graph 1 (Maximize Production)')
    # Heuristics of minimizing waste
    save_path = f'{OUTPUT_DIR}/complex_graph_1_waste'
    problem_waste.optimize()
    problem_waste.create_graph()
    # problem_waste.print_graph()
    problem_waste.visualize_graph(save_path, 'Complex Graph 1 (Minimize Waste)')
    # Heuristics of maximizing target production with penalty of waste
    save_path = f'{OUTPUT_DIR}/complex_graph_1_value_and_waste'
    problem_PnW.optimize()
    problem_PnW.create_graph()
    # problem_PnW.print_graph()
    problem_PnW.visualize_graph(save_path, 'Complex Graph 1 (Production Penalized with Waste)')

def run_complex_example_2():
    problem_produce = DemoProblems.complex_example_2(ObjMethods.S_VALUE)
    problem_waste = DemoProblems.complex_example_2(ObjMethods.S_WASTE)
    problem_PnW = DemoProblems.complex_example_2(ObjMethods.S_VALUE_WASTE)
        
    if not problem_produce.validate():
        print("Problem (Produce) is invalid")
        return
    if not problem_waste.validate():
        print("Problem (Waste) is invalid")
        return
    if not problem_PnW.validate():
        print("Problem (Produce and Waste) is invalid")
        return
    
    # Create output_png folder if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Heuristics of maximizing target production
    save_path = f'{OUTPUT_DIR}/complex_graph_2_value'
    problem_produce.optimize()
    problem_produce.create_graph()
    # problem_produce.print_graph()
    problem_produce.visualize_graph(save_path, 'Complex Graph 2 (Maximize Production)')
    # Heuristics of minimizing waste
    save_path = f'{OUTPUT_DIR}/complex_graph_2_waste'
    problem_waste.optimize()
    problem_waste.create_graph()
    # problem_waste.print_graph()
    problem_waste.visualize_graph(save_path, 'Complex Graph 2 (Minimize Waste)')
    # Heuristics of maximizing target production with penalty of waste
    save_path = f'{OUTPUT_DIR}/complex_graph_2_value_and_waste'
    problem_PnW.optimize()
    problem_PnW.create_graph()
    # problem_PnW.print_graph()
    problem_PnW.visualize_graph(save_path, 'Complex Graph 2 (Production Penalized with Waste)')

def main():
    run_complex_example_1()
    run_complex_example_2()

if __name__ == "__main__":
    main()
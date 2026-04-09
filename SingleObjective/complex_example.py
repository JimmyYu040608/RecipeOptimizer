import os
from src.demo_data import DemoProblems
from src.utils import ObjMethods

OUTPUT_DIR = "./images/soo"

def main():
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
    save_path = f'{OUTPUT_DIR}/production_graph_value'
    problem_produce.optimize()
    problem_produce.create_graph()
    # problem_produce.print_graph()
    problem_produce.visualize_graph(save_path, 'Production Graph (Maximize Production)')
    # Heuristics of minimizing waste
    save_path = f'{OUTPUT_DIR}/production_graph_waste'
    problem_waste.optimize()
    problem_waste.create_graph()
    # problem_waste.print_graph()
    problem_waste.visualize_graph(save_path, 'Production Graph (Minimize Waste)')
    # Heuristics of maximizing target production with penalty of waste
    save_path = f'{OUTPUT_DIR}/production_graph_value_and_waste'
    problem_PnW.optimize()
    problem_PnW.create_graph()
    # problem_PnW.print_graph()
    problem_PnW.visualize_graph(save_path, 'Production Graph (Production Penalized with Waste)')

if __name__ == "__main__":
    main()
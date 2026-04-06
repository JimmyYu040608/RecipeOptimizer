import time
from src.common import ObjMethods
from src.demo_data import DemoProblems

OUTPUT_DIR = "./images/eval"

def main():
    """ Run example_5 problems with different obj methods """
    
    # Heuristics of maximizing target production
    print("\n1. Optimizing for Maximum Production Value...")
    problem_value = DemoProblems.example_5(ObjMethods.S_VALUE)
    save_path = f'{OUTPUT_DIR}/example_5_graph_value'
    start_time = time.perf_counter()
    problem_value.optimize()
    opt_time = time.perf_counter() - start_time
    print(f"Optimization completed in {opt_time:.4f} seconds")
    problem_value.create_graph()
    graph_time = time.perf_counter() - start_time
    print(f"Graph creation completed in {graph_time - opt_time:.4f} seconds")
    # problem_value.print_graph()
    problem_value.visualize_graph(save_path, 'Example 5: Maximize Production Value')
    end_time = time.perf_counter()
    print(f"Total time taken: {end_time - start_time:.4f} seconds")
    
    # Heuristics of minimizing waste
    print("\n2. Optimizing for Minimum Waste...")
    problem_waste = DemoProblems.example_5(ObjMethods.S_WASTE)
    save_path = f'{OUTPUT_DIR}/example_5_graph_waste'
    start_time = time.perf_counter()
    problem_waste.optimize()
    opt_time = time.perf_counter() - start_time
    print(f"Optimization completed in {opt_time:.4f} seconds")
    problem_waste.create_graph()
    graph_time = time.perf_counter() - start_time
    print(f"Graph creation completed in {graph_time - opt_time:.4f} seconds")
    # problem_waste.print_graph()
    problem_waste.visualize_graph(save_path, 'Example 5: Minimize Waste')
    end_time = time.perf_counter()
    print(f"Total time taken: {end_time - start_time:.4f} seconds")
    
    # Heuristics of maximizing target production with penalty of waste
    print("\n3. Optimizing for Production Value with Waste Penalty with Single Objective Function...")
    problem_VnW = DemoProblems.example_5(ObjMethods.S_VALUE_WASTE)
    save_path = f'{OUTPUT_DIR}/example_5_graph_soo_value_waste'
    start_time = time.perf_counter()
    problem_VnW.optimize()
    opt_time = time.perf_counter() - start_time
    print(f"Optimization completed in {opt_time:.4f} seconds")
    problem_VnW.create_graph()
    graph_time = time.perf_counter() - start_time
    print(f"Graph creation completed in {graph_time - opt_time:.4f} seconds")
    # problem_VnW.print_graph()
    problem_VnW.visualize_graph(save_path, 'Example 5: Production Penalized with Waste')
    end_time = time.perf_counter()
    print(f"Total time taken: {end_time - start_time:.4f} seconds")
    
    # Heuristics of maximizing target production and minimizing waste with Multi-Objective Optimization (Pareto Front)
    print("\n4. Optimizing for Production Value and Waste with Multi-Objective Optimization (Pareto Front)...")
    problem_MVnW = DemoProblems.example_5(ObjMethods.M_VALUE_WASTE)
    save_path = f'{OUTPUT_DIR}/example_5_graph_m_value_waste'
    start_time = time.perf_counter()
    problem_MVnW.optimize()
    opt_time = time.perf_counter() - start_time
    print(f"Optimization completed in {opt_time:.4f} seconds")
    problem_MVnW.create_graph()
    graph_time = time.perf_counter() - start_time
    print(f"Graph creation completed in {graph_time - opt_time:.4f} seconds")
    # problem_MVnW.print_graph()
    problem_MVnW.visualize_graph(save_path, 'Example 5: Multi-Objective Optimization (Value and Waste)')
    end_time = time.perf_counter()
    print(f"Total time taken: {end_time - start_time:.4f} seconds")
    
    print("\nExample 5 evaluation complete!")

if __name__ == "__main__":
    main()
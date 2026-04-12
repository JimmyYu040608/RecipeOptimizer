from src.demo_data import DemoProblems
from eval.eval_process import default_method_configs, run_evaluation
from eval.comparison import plot_comparison

METHOD_GRAPH_ROOT = "./images/eval"
COMPARISON_ROOT = "./images/eval/comparison"

def small_example():
    """Evaluate the small example (the real tag in DemoProblems is complex_example) with shared dynamic evaluation pipeline."""
    
    config_small = default_method_configs("small_example", "Small Example")
    
    return run_evaluation(
        problem_factory=DemoProblems.complex_example,
        method_configs=config_small,
        evaluation_name="Small Example Evaluation",
        output_dir=f"{METHOD_GRAPH_ROOT}/small_example",
    )

def single_large_example():
    """Evaluate the single large example with shared dynamic evaluation pipeline."""
    
    config_large = default_method_configs("single_large_example", "Single Large Example")
    
    return run_evaluation(
        problem_factory=DemoProblems.single_large_example,
        method_configs=config_large,
        evaluation_name="Single Large Example Evaluation",
        output_dir=f"{METHOD_GRAPH_ROOT}/single_large_example",
    )

def eval_example_5():
    """Evaluate example 5 with shared dynamic evaluation pipeline."""
    
    config_5 = default_method_configs("example_5", "Example-5")
    
    return run_evaluation(
        problem_factory=DemoProblems.example_5,
        method_configs=config_5,
        evaluation_name="Example-5 Evaluation",
        output_dir=f"{METHOD_GRAPH_ROOT}/example_5",
    )

def eval_example_12():
    """Evaluate example-12 with shared dynamic evaluation pipeline."""
    
    config_12 = default_method_configs("example_12", "Example-12")
    
    return run_evaluation(
        problem_factory=DemoProblems.example_12,
        method_configs=config_12,
        evaluation_name="Example-12 Evaluation",
        output_dir=f"{METHOD_GRAPH_ROOT}/example_12",
    )
    
def main():
    """ Run all evaluations and plot per-evaluation 4-metric comparisons. """
    small_results = small_example()
    plot_comparison(
        small_results,
        title="Small Example: Value, Waste, Power, and Time by Method",
        output_path=f"{COMPARISON_ROOT}/small_example_comparison.png",
    )

    large_results = single_large_example()
    plot_comparison(
        large_results,
        title="Single Large Example: Value, Waste, Power, and Time by Method",
        output_path=f"{COMPARISON_ROOT}/single_large_example_comparison.png",
    )

    example5_results = eval_example_5()
    plot_comparison(
        example5_results,
        title="Example-5: Value, Waste, Power, and Time by Method",
        output_path=f"{COMPARISON_ROOT}/example_5_comparison.png",
    )

    # eval_example_12()

if __name__ == "__main__":
    main()
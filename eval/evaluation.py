from src.demo_data import DemoProblems
from eval.eval_process import default_method_configs, run_evaluation

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
        log_path=f"{METHOD_GRAPH_ROOT}/small_example/log.json",
    )

def medium_example():
    """Evaluate the medium example with shared dynamic evaluation pipeline."""
    
    config_medium = default_method_configs("medium_example", "Medium Example")
    
    return run_evaluation(
        problem_factory=DemoProblems.complex_example_2,
        method_configs=config_medium,
        evaluation_name="Medium Example Evaluation",
        output_dir=f"{METHOD_GRAPH_ROOT}/medium_example",
        log_path=f"{METHOD_GRAPH_ROOT}/medium_example/log.json",
    )

def single_large_example():
    """Evaluate the single large example with shared dynamic evaluation pipeline."""
    
    config_large = default_method_configs("single_large_example", "Single Large Example")
    
    return run_evaluation(
        problem_factory=DemoProblems.single_large_example,
        method_configs=config_large,
        evaluation_name="Single Large Example Evaluation",
        output_dir=f"{METHOD_GRAPH_ROOT}/single_large_example",
        log_path=f"{METHOD_GRAPH_ROOT}/single_large_example/log.json",
    )

def eval_example_5():
    """Evaluate example 5 with shared dynamic evaluation pipeline."""
    
    config_5 = default_method_configs("example_5", "Example-5")
    
    return run_evaluation(
        problem_factory=DemoProblems.example_5,
        method_configs=config_5,
        evaluation_name="Example-5 Evaluation",
        output_dir=f"{METHOD_GRAPH_ROOT}/example_5",
        log_path=f"{METHOD_GRAPH_ROOT}/example_5/log.json",
    )

def eval_example_12():
    """Evaluate example-12 with shared dynamic evaluation pipeline."""
    
    config_12 = default_method_configs("example_12", "Example-12")
    
    return run_evaluation(
        problem_factory=DemoProblems.example_12,
        method_configs=config_12,
        evaluation_name="Example-12 Evaluation",
        output_dir=f"{METHOD_GRAPH_ROOT}/example_12",
        log_path=f"{METHOD_GRAPH_ROOT}/example_12/log.json",
    )
    
def main():
    """ Run evaluations only. Plotting is handled by eval.evaluate_log from JSON logs. """
    small_example()
    medium_example()
    single_large_example()
    eval_example_5()
    # eval_example_12()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Evaluation interrupted by user.")
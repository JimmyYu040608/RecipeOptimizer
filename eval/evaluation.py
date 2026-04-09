from src.demo_data import DemoProblems
from eval.eval_process import default_method_configs, run_evaluation

def small_example():
    """Evaluate the small example (the real tag in DemoProblems is complex_example) with shared dynamic evaluation pipeline."""
    
    config_small = default_method_configs("small_example", "Small Example")
    
    run_evaluation(
        problem_factory=DemoProblems.complex_example,
        method_configs=config_small,
        evaluation_name="Small Example Evaluation",
    )

def single_large_example():
    """Evaluate the single large example with shared dynamic evaluation pipeline."""
    
    config_large = default_method_configs("single_large_example", "Single Large Example")
    
    run_evaluation(
        problem_factory=DemoProblems.single_large_example,
        method_configs=config_large,
        evaluation_name="Single Large Example Evaluation",
    )

def eval_example_5():
    """Evaluate example 5 with shared dynamic evaluation pipeline."""
    
    config_5 = default_method_configs("example_5", "Example-5")
    
    run_evaluation(
        problem_factory=DemoProblems.example_5,
        method_configs=config_5,
        evaluation_name="Example-5 Evaluation",
    )

def eval_example_12():
    """Evaluate example-12 with shared dynamic evaluation pipeline."""
    
    config_12 = default_method_configs("example_12", "Example-12")
    
    run_evaluation(
        problem_factory=DemoProblems.example_12,
        method_configs=config_12,
        evaluation_name="Example-12 Evaluation",
    )
    
def main():
    """ Run all evaluations"""
    small_example()
    single_large_example()
    eval_example_5()
    # eval_example_12()

if __name__ == "__main__":
    main()
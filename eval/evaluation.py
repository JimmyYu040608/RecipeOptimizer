from src.demo_data import DemoProblems
from eval.eval_process import default_method_configs, run_evaluation

def eval_example_5():
    """Evaluate example 5 with shared dynamic evaluation pipeline."""
    
    config_5 = default_method_configs("example_5", "Example-5")
    
    run_evaluation(
        problem_factory=DemoProblems.example_5,
        method_configs=config_5,
        evaluation_name="Example-5 evaluation",
    )

def eval_example_12():
    """Evaluate example-12 with shared dynamic evaluation pipeline."""
    
    config_12 = default_method_configs("example_12", "Example-12")
    
    run_evaluation(
        problem_factory=DemoProblems.example_12,
        method_configs=config_12,
        evaluation_name="Example-12 evaluation",
    )
    
def main():
    """ Run all evaluations"""
    eval_example_5()
    # eval_example_12()

if __name__ == "__main__":
    main()
# ProductionLineOptimizer

Demonstration of production line optimization and production graph generation by maximizing production of target products according to priorities and minimizing waste.

## Getting Started

This section brings you through setting up the environment for using ProductionLineOptimizer.

### Python Libraries

- Python 3.11.9 or higher
- All required libraries are specified in 'requirements.txt'
  ```
  pip install -r requirements.txt
  ```

### External Applications

- Graphviz is used in this program to generate graphs
- Install Graphviz according to the instructions in https://graphviz.org/download/
- Add the directory containing binaries of Graphviz to PATH

## Usage

- To run demonstration scripts, first go into the ProductionLineOptimizer directory
  ```
  cd ProductionLineOptimizer
  ```
- Single-objective optimization examples demonstrate various scenarios from simple to complex cases
  ```
  py -m SingleObjective.simple_example
  py -m SingleObjective.demo
  py -m SingleObjective.complex_example
  py -m SingleObjective.extraordinary_example
  ```
- Multi-objective optimization example demonstrates value-waste tradeoff
  ```
  py -m MultiObjective.value_waste_example
  ```
- Custom graph drawing utility for creating production topology visualizations
  ```
  py custom_draw.py
  ```
- Evaluation and comparison utilities
  ```
  py -m eval.comparison
  ```

## Repository Structure

```text
/ProductionLineOptimizer
├── /resources
│   └── data.json               # Contain all data (recipes, items, etc) in game Satisfactory
│
├── /src
│   ├── common.py               # Create functions for general use
│   ├── recipe.py               # Define data structures and functions for recipe data
│   ├── graph.py                # Define data structures and functions for graphs
│   ├── solver.py               # Solve optimization problem to generate the resulting production graph
│   └── shared_setup.py         # Shared setup utilities for creating demo problems
│
├── /SingleObjective
│   ├── simple_example.py       # Simple single-objective optimization examples
│   ├── demo.py                 # Various demonstration examples
│   ├── complex_example.py      # Complex production scenarios
│   └── extraordinary_example.py # Edge cases and special scenarios
│
├── /MultiObjective
│   ├── /src
│   │   ├── pick_best_pareto.py # Pareto optimal solution selection
│   │   └── weight_estimate.py  # Weight estimation for multi-objective optimization
│   └── value_waste_example.py  # Value-waste tradeoff optimization example
│
├── /eval
│   └── comparison.py           # Comparison and plotting utilities for evaluation
│
├── /images                     # Generated visualization outputs
│   ├── /demo                   # Demo example outputs
│   ├── /draw                   # Custom drawing outputs
│   ├── /moo                    # Multi-objective optimization outputs
│   └── /soo                    # Single-objective optimization outputs
│
├── custom_draw.py              # Custom graph drawing utilities
├── requirements.txt            # Python dependencies
├── .gitignore
└── README.md
```
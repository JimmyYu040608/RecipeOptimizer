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

- To run demonstration scripts, first go into the directory of where main.py rooted in
  ```
  cd ProductionLineOptimizer
  ```
- main.py demonstrates a typical example with the processes from loading data to generating the resulting optimized production graph
  ```
  py main.py
  ```
- demo.py demonstrates other examples, from the simplest examples to some special cases, and how optimization affects the resulting production graph
  ```
  py demo.py
  ```

## Repository Structure

```text
/ProductionLineOptimizer
├── /resources
│   └── data.json       # Contain all data (recipes, items, etc) in game Satisfactory
│
├── /src
│   ├── common.py       # Create functions for general use
│   ├── recipe.py       # Define data structures and functions for recipe data
│   ├── graph.py        # Define data structures and functions for graphs
│   └── solver.py       # Solve optimization problem to generate the resulting production graph
│
├── main.py             # Demonstrate a normal example of how the program will work
├── demo.py             # Demonstrate various examples, from simplest ones to special cases
├── .gitignore
└── README.md
```
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
- Multi-objective optimization example demonstrates value-waste tradeoff using weighted sum method
  ```
  py -m MultiObjective.value_waste_example
  ```
- Custom graph drawing utility for creating production topology visualizations (for debugging)
  ```
  py custom_draw.py
  ```
- Evaluation and comparison utilities for plotting production vs waste metrics
  ```
  py -m eval.comparison
  ```

## Features

### Optimization Methods

- **Single-Objective Optimization (SOO)**
  - Maximize production value of target products
  - Minimize waste of intermediate products
  - Combined objective with waste penalty (weighted approach)

- **Multi-Objective Optimization (MOO)**
  - Pareto front generation using weighted sum method
  - Automatic best solution selection based on utopia point distance
  - Normalized objective functions for balanced optimization

### Graph Visualization

- Production flow graphs with color-coded nodes and edges
- Source nodes (blue) → Machine nodes (box) → Sink nodes (green)
- Waste nodes (red) for tracking inefficiencies
- Automatic graph generation using Graphviz

### Problem Validation

- Recipe dependency validation
- Input-output feasibility checking
- Automatic problem reduction to remove irrelevant recipes

## Repository Structure

```text
/ProductionLineOptimizer
├── /resources
│   └── data.json               # Game data from Satisfactory (recipes, items, buildings)
│
├── /src
│   ├── common.py               # Common utilities (rounding, method types, weight generation)
│   ├── recipe.py               # Recipe, Product, Building classes and data loading
│   ├── graph.py                # Graph structures (vertices, edges) and visualization
│   ├── solver.py               # Optimization solver using OR-Tools (SCIP)
│   └── shared_setup.py         # Demo problem setup utilities
│
├── /SingleObjective
│   ├── simple_example.py       # Simple examples with manual and optimized solutions
│   ├── demo.py                 # Quick demonstration example
│   ├── complex_example.py      # Complex fuel production scenario
│   └── extraordinary_example.py # Modular engine production scenario
│
├── /MultiObjective
│   ├── /src
│   │   ├── pick_best_pareto.py # Utopia point-based Pareto solution selection
│   │   └── weight_estimate.py  # Normalization parameters for weighted sum method
│   └── value_waste_example.py  # Value-waste tradeoff optimization
│
├── /eval
│   └── comparison.py           # Comparison plotting utilities using matplotlib
│
├── /images                     # Generated visualization outputs
│   ├── /demo                   # Demo example outputs
│   ├── /draw                   # Custom drawing outputs
│   ├── /moo                    # Multi-objective optimization outputs
│   └── /soo                    # Single-objective optimization outputs
│
├── custom_draw.py              # Custom graph drawing utilities using graphviz
├── requirements.txt            # Python dependencies
├── .gitignore
└── README.md
```

## Technical Details

### Solver Configuration

- Uses OR-Tools SCIP solver for mixed-integer linear programming
- Configurable constraints:
  - `RECIPE_MAX`: Maximum instances of any recipe (default: 100)
  - `PRODUCT_MAX`: Maximum production rate of any product (default: 10000)
  - `RECIPE_COST`: Small penalty to discourage unnecessary recipes (default: 0.01)

### Data Structures

- **Product**: Represents items with name and sink point value
- **Recipe**: Defines input/output rates and building requirements
- **Vertices**: SourceVertex, SinkVertex, MachineVertex, WasteVertex
- **FlowEdge**: Represents product flow between vertices with provide/consume rates

### Optimization Objectives

1. **S_VALUE**: Maximize `Σ(product_rate × score)` for target products
2. **S_WASTE**: Minimize `Σ(waste_rate × sink_points)` for non-target products
3. **S_VALUE_WASTE**: Combined objective with fixed waste penalty weight
4. **M_VALUE_WASTE**: Multi-objective with Pareto front exploration (21 weight combinations)

## Example Problems

### Demo Problem
- **Inputs**: Iron Ingot (120/min), Copper Ingot (60/min)
- **Outputs**: Reinforced Iron Plate (score: 1000), Copper Wire (score: 20)
- **Recipes**: Iron Screw, Copper Screw, Iron Plate, Reinforced Iron Plate, Copper Wire

### Complex Example (Fuel Production)
- **Inputs**: Crude Oil (300/min), Water (800/min), Coal (533.33/min), Sulfur (533.33/min)
- **Outputs**: Fuel (score: 600), Turbofuel (score: 2000)

### Extraordinary Example (Modular Engine)
- **Inputs**: Iron Ore (1000/min), Copper Ore (800/min), Coal (900/min), Crude Oil (500/min)
- **Outputs**: Modular Engine (score: 1000)

## Dependencies

- `absl-py==2.3.1` - Abseil Python library
- `graphviz==0.21` - Graph visualization
- `immutabledict==4.2.2` - Immutable dictionary structures
- `numpy==2.3.5` - Numerical computing
- `ortools==9.14.6206` - Optimization solver
- `pandas==2.3.3` - Data manipulation
- `protobuf==6.31.1` - Protocol buffers
- `python-dateutil==2.9.0.post0` - Date utilities
- `pytz==2025.2` - Timezone support
- `six==1.17.0` - Python 2/3 compatibility
- `typing_extensions==4.15.0` - Type hints
- `tzdata==2025.2` - Timezone data

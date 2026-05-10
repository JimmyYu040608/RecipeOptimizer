# ProductionLineOptimizer

Demonstration of production line optimization and production graph generation by maximizing production of target products according to priorities while minimizing waste and power consumption.

## Getting Started

This section brings you through setting up the environment for using ProductionLineOptimizer.

### Python Libraries

- Python 3.11.9 or higher
- All required libraries are specified in `requirements.txt`
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
- Multi-objective optimization example demonstrates value-waste tradeoff using weighted metric method
  ```
  py -m MultiObjective.value_waste_example
  ```
- Custom graph drawing utility for creating production topology visualizations (for debugging)
  ```
  py custom_draw.py
  ```
- Evaluation pipeline — runs all benchmark problems across all objective methods, writes JSON logs
  ```
  py -m eval.evaluation
  ```
- Plot comparison charts from previously written evaluation logs (no re-solving required)
  ```
  py -m eval.evaluate_log
  ```

## Features

### Optimization Methods

- **Single-Objective Optimization (SOO)**
  - Maximize production value of target products
  - Minimize waste of intermediate products
  - Combined objective with waste penalty
  - Combined objective with power penalty
  - Combined objective with both waste and power penalties

- **Multi-Objective Optimization (MOO)**
  - Pareto front generation using weighted metric method
  - Value + Waste two-objective optimization
  - Value + Waste + Power three-objective optimization
  - Automatic best solution selection based on normalized utopia point distance

### Graph Visualization

- Production flow graphs with color-coded nodes and edges
- Source nodes (blue) → Machine nodes (box) → Sink nodes (green)
- Waste nodes (red) for tracking inefficiencies
- Automatic graph generation using Graphviz

### Problem Validation

- Recipe dependency validation
- Input-output feasibility checking
- Automatic problem reduction to remove irrelevant recipes
- Reversible recipe pair detection and mutual-exclusion enforcement

## Repository Structure

```text
/ProductionLineOptimizer
├── /resources
│   ├── data.json               # Game data from Satisfactory (legacy)
│   └── data_1.1.json           # Updated game data from Satisfactory (recipes, items, buildings)
│
├── /src
│   ├── utils.py                # Utilities (rounding, MethodTypes, ObjMethods, weight generation)
│   ├── recipe.py               # Recipe, Product, Building classes and data loading
│   ├── graph.py                # Graph structures (vertices, edges) and visualization
│   ├── solver.py               # Optimization solver using OR-Tools (SCIP)
│   ├── demo_data.py            # Demo problem definitions (DemoItems, DemoRecipes, DemoProblems)
│   └── /multi_objective
│       ├── pick_best_pareto.py # Utopia point-based Pareto solution selection
│       └── weight_estimate.py  # Normalization parameters for weighted metric method
│
├── /SingleObjective
│   ├── simple_example.py       # Simple examples with manual and optimized solutions
│   ├── demo.py                 # Quick demonstration example
│   ├── complex_example.py      # Complex fuel production scenario
│   └── extraordinary_example.py # Modular engine production scenario
│
├── /MultiObjective
│   └── value_waste_example.py  # Value-waste tradeoff MOO demonstration
│
├── /eval
│   ├── eval_process.py         # Core evaluation infrastructure (MethodConfig, run_evaluation)
│   ├── evaluation.py           # Benchmark runner — solves all problems and writes JSON logs
│   ├── evaluate_log.py         # Reads JSON logs and generates comparison bar charts
│   └── comparison.py           # Standalone comparison plotting utilities
│
├── /images                     # Generated visualization outputs
│   ├── /demo                   # Demo example outputs
│   ├── /draw                   # Custom drawing outputs
│   ├── /eval                   # Evaluation comparison charts
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
- Configurable constants in `solver.py`:
  - `RECIPE_MAX`: Maximum instances of any single recipe (default: 100)
  - `PRODUCT_MAX`: Maximum production rate of any single product (default: 10000)
  - `RECIPE_COST`: Small penalty to discourage extraneous recipes (default: 0.01)
  - `ALT_PENALTY`: Extra penalty for using alternate recipes (default: 1e-6)
  - `WASTE_PENALTY`: Weight of waste in single-objective combined methods (default: 1)
  - `POWER_PENALTY`: Weight of power in single-objective combined methods (default: 1)
  - `PARETO_RESOLUTION`: Sampling resolution for weighted-metric MOO (default: 20)

### Data Structures

- **Building**: Represents a machine type with name and power consumption
- **Product**: Represents items with name and sink point value
- **Recipe**: Defines input/output rates, building type, alternate flag, and per-instance power cost
- **Vertices**: `SourceVertex`, `SinkVertex`, `MachineVertex`, `WasteVertex`
- **FlowEdge**: Represents product flow between vertices with provide/consume rates

### Optimization Objectives

| ID | Class | Description |
|----|-------|-------------|
| `S_VALUE` | SOO | Maximize `Σ(production_rate × score)` for target products |
| `S_WASTE` | SOO | Minimize `Σ(leftover_rate)` for non-target products |
| `S_VALUE_WASTE` | SOO | Maximize value with fixed waste penalty |
| `S_VALUE_POWER` | SOO | Maximize value with fixed power-consumption penalty |
| `S_VALUE_WASTE_POWER` | SOO | Maximize value with both waste and power penalties |
| `M_VALUE_WASTE` | MOO | Weighted-metric Pareto exploration over value and waste |
| `M_VALUE_WASTE_POWER` | MOO | Weighted-metric Pareto exploration over value, waste, and power |

MOO methods normalize each objective to [0, 1] and select the solution closest to the utopia point.

### Evaluation Pipeline

`eval/eval_process.py` provides:
- `MethodConfig` — describes a single method run (name, objective, graph settings, timeout)
- `MethodEvaluationResult` — stores outcome metrics (value, waste, power, time, weights)
- `default_method_configs()` — creates a standard 7-method configuration set
- `run_evaluation()` — executes all methods for a problem, writes a `log.json`

`eval/evaluation.py` runs the benchmark problems and writes logs:
```
py -m eval.evaluation
```

`eval/evaluate_log.py` reads the JSON logs and generates comparison bar charts without re-solving:
```
py -m eval.evaluate_log
```

## Example Problems

### Demo Problem (`DemoProblems.demo_example`)
- **Inputs**: Iron Ingot (120/min), Copper Ingot (60/min)
- **Outputs**: Reinforced Iron Plate (score: 1000), Copper Wire (score: 20)
- **Recipes**: Iron Screw, Copper Screw, Iron Plate, Reinforced Iron Plate, Copper Wire

### Small Example (`DemoProblems.complex_example`)
- **Inputs**: Crude Oil (300/min), Water (800/min), Coal (533.33/min), Sulfur (533.33/min)
- **Outputs**: Fuel (score: 600), Turbofuel (score: 2000)

### Medium Example (`DemoProblems.complex_example_2`)
- **Inputs**: Iron Ore (1000/min), Copper Ore (800/min), Coal (700/min), Limestone (700/min)
- **Outputs**: Heavy Modular Frame (score: 10800), Stator (score: 240)

### Single Large Example (`DemoProblems.single_large_example`)
- **Inputs**: Iron Ore (1000/min), Copper Ore (800/min), Coal (900/min), Crude Oil (500/min)
- **Outputs**: Modular Engine (score: 1000)

### Example-5 (`DemoProblems.example_5`)
- **Inputs**: Iron Ore (2000/min), Copper Ore (1000/min), Coal (1000/min), Limestone (500/min), Wood (180/min), Water (600/min), Crude Oil (100/min)
- **Outputs**: Smart Plating, Versatile Framework, Automated Wiring, Modular Engine, Adaptive Control Unit

### Example-12 (`DemoProblems.example_12`)
- 14-input, 12-output large-scale benchmark covering most Satisfactory end-game items (Smart Plating → AI Expansion Server)

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

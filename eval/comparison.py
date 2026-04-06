import matplotlib.pyplot as plt
from typing import List

class PlotResult:
    def __init__(self, method_name: str, production: float, waste: float):
        self.method_name = method_name
        self.production = production
        self.waste = waste

def plot_comparison(data: List[PlotResult]):
    # Plot dual-axis bars: left axis for Value, right axis for Waste
    
    # Extract data
    methods = [d.method_name for d in data]
    value = [d.production for d in data]
    waste = [d.waste for d in data]
    
    x = range(len(methods))
    width = 0.35
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    bars_value = ax1.bar(
        [i - width / 2 for i in x], value, width,
        label='Value', color='tab:blue', alpha=0.85
    )
    bars_waste = ax2.bar(
        [i + width / 2 for i in x], waste, width,
        label='Waste', color='tab:orange', alpha=0.85
    )

    ax1.set_xlabel('Method')
    ax1.set_ylabel('Value', color='tab:blue')
    ax2.set_ylabel('Waste', color='tab:orange')
    ax1.set_title('Value vs Waste Comparison Across Methods')
    ax1.set_xticks(x)
    ax1.set_xticklabels(methods, rotation=45, ha='right')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax2.tick_params(axis='y', labelcolor='tab:orange')

    # Merge legends from both axes
    handles = [bars_value, bars_waste]
    labels = [h.get_label() for h in handles]
    ax1.legend(handles, labels, loc='upper left')
    ax1.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    # Example usage
    data = [
        PlotResult('SOO Value', 100, 10),
        PlotResult('SOO Waste', 80, 5),
        PlotResult('SOO Value-Waste', 90, 15),
        PlotResult('MOO Value-Waste', 95, 12)
    ]

    plot_comparison(data)
import matplotlib.pyplot as plt
from typing import List

class PlotData:
    def __init__(self, method_name: str, production: float, waste: float):
        self.method_name = method_name
        self.production = production
        self.waste = waste

def plot_comparison(data: List[PlotData]):
    # Plot grouped bar charts (value vs waste) over all methods
    
    # Extract data
    methods = [d.method_name for d in data]
    production = [d.production for d in data]
    waste = [d.waste for d in data]
    
    x = range(len(methods))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar([i - width/2 for i in x], production, width, label='Production')
    ax.bar([i + width/2 for i in x], waste, width, label='Waste')
    
    ax.set_xlabel('Method')
    ax.set_ylabel('Value')
    ax.set_title('Production vs Waste Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    # Example usage
    data = [
        PlotData('SOO Value', 100, 10),
        PlotData('SOO Waste', 80, 5),
        PlotData('SOO Value-Waste', 90, 15),
        PlotData('MOO Value-Waste', 95, 12)
    ]

    plot_comparison(data)
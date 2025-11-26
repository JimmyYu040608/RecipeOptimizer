import graphviz

class GraphDrawer:
    def __init__(self, title="temp_graph", size='20', format="png"):
        self.graph = graphviz.Digraph(comment=title, format=format)
        self.graph.attr(label=title, fontsize=size, labelloc='t', fontname='Helvetica-Bold')
    
    def add_node(self, node_id, label=None, **attrs):
        """Add a node to the graph"""
        if label is None:
            label = str(node_id)
        self.graph.node(str(node_id), label, **attrs)
        
    def add_input_node(self, node_id, label=None, **attrs):
        """Add an input node"""
        attrs['color'] = 'blue'
        self.add_node(node_id, label, **attrs)
    
    def add_machine_node(self, node_id, label=None, **attrs):
        """Add a machine node"""
        attrs['shape'] = 'box'
        self.add_node(node_id, label, **attrs)
    
    def add_output_node(self, node_id, label=None, **attrs):
        """Add an output node"""
        attrs['color'] = 'green'
        self.add_node(node_id, label, **attrs)
    
    def add_waste_node(self, node_id, label=None, **attrs):
        """Add a waste node"""
        attrs['color'] = 'red'
        self.add_node(node_id, label, **attrs)
    
    def add_edge(self, from_node, to_node, label=None, **attrs):
        """Add an edge between two nodes"""
        if label:
            self.graph.edge(str(from_node), str(to_node), label, **attrs)
        else:
            self.graph.edge(str(from_node), str(to_node), **attrs)
    
    def add_blue_edge(self, from_node, to_node, label=None):
        """Add a blue edge between two nodes"""
        attrs = {'color': 'blue', 'fontcolor': 'blue'}
        self.add_edge(from_node, to_node, label, **attrs)
    
    def add_green_edge(self, from_node, to_node, label=None):
        """Add a green edge between two nodes"""
        attrs = {'color': 'green', 'fontcolor': 'green'}
        self.add_edge(from_node, to_node, label, **attrs)
    
    def add_red_edge(self, from_node, to_node, label=None):
        """Add a red edge between two nodes"""
        attrs = {'color': 'red', 'fontcolor': 'red'}
        self.add_edge(from_node, to_node, label, **attrs)
    
    def render(self, filename=None, view=True):
        """Render and optionally view the graph"""
        if filename:
            self.graph.render(filename, view=view, cleanup=True)
        else:
            self.graph.render(view=view, cleanup=True)
    
    def save_source(self, filename):
        """Save the DOT source code"""
        with open(filename, 'w') as f:
            f.write(self.graph.source)


def combined_iron_plate():
    drawer = GraphDrawer("Combined Iron Plate", '16')
    
    drawer.add_node("1", "Iron Plate", color="blue")
    drawer.add_node("2", "Screw", color="blue")
    drawer.add_node("3", "Combined Iron Plate", shape="box")
    drawer.add_node("4", "Combined Iron Plate", color="green")
    
    drawer.add_edge("1", "3", color="blue", fontcolor="blue")
    drawer.add_edge("2", "3", color="blue", fontcolor="blue")
    drawer.add_edge("3", "4", color="green", fontcolor="green")
    
    drawer.render("example_png/combined_iron_plate", view=False)


def reinforced_iron_plate():
    drawer = GraphDrawer("Reinforced Iron Plate", '16')
    
    drawer.add_input_node("1", "Iron Ingot")
    drawer.add_machine_node("2", "Iron Screw")
    drawer.add_machine_node("3", "Iron Plate")
    drawer.add_machine_node("4", "Reinforced Iron Plate")
    drawer.add_output_node("5", "Reinforced Iron Plate")
    
    drawer.add_blue_edge("1", "2")
    drawer.add_blue_edge("1", "3")
    drawer.add_edge("2", "4")
    drawer.add_edge("3", "4")
    drawer.add_green_edge("4", "5")
    
    drawer.render("example_png/reinforced_iron_plate", view=False)

    
def main():
    combined_iron_plate()
    reinforced_iron_plate()
    return


if __name__ == "__main__":
    main()
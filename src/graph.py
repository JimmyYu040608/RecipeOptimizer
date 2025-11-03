from typing import List, Dict
from src.recipe import Product, Recipe


class MachineVertex:
    """ Represents a machine (vertex) on the graph where production with a recipe is taken place """
    def __init__(self, recipe: Recipe, scale: int):
        self.recipe = recipe
        # Enforce only int for scale
        if not isinstance(scale, int):
            raise ValueError("Scale must be an integer")
        self.scale = scale
        self.in_flows: List[FlowEdge] = []
        self.out_flows: List[FlowEdge] = []
    
    def in_demands(self) -> Dict[Product, float]:
        """ Calcute expected in-flows of this machine according to recipe and scale """
        # Scale up each product rate according to scale
        return {product: rate * self.scale for product, rate in self.recipe.inputs}
    
    def out_demands(self) -> Dict[Product, float]:
        """ Calcute expected out-flows of this machine according to recipe and scale """
        # Scale up each product rate according to scale
        return {product: rate * self.scale for product, rate in self.recipe.outputs}
    
    def satisfied(self) -> bool:
        """ Check if all in-demands are satisfied by in-flows """
        in_demands = self.in_demands()
        # Check all demands
        for product, demand in in_demands.items():
            # Sum all flows of that product
            total_rate = sum([flow.rate for flow in self.in_flows if flow.product == product])
            if total_rate < demand:
                return False
        return True


class FlowEdge:
    """ Represents a flow (edge) on the graph that is moving from one machine to another """
    def __init__(self, product: Product, rate: float, src: MachineVertex, dst: MachineVertex):
        self.product = product
        self.rate = rate
        self.src = src
        self.dst = dst


class ProductionGraph:
    """ A graph for the whole production line """
    def __init__(self):
        self.vertices: List[MachineVertex] = []
        self.edges: List[FlowEdge] = []
    
    def add_vertex(self, vertex: MachineVertex):
        self.vertices.append(vertex)
    
    def add_edge(self, edge: FlowEdge):
        self.edges.append(edge)
        edge.src.out_flows.append(edge)
        edge.dst.in_flows.append(edge)
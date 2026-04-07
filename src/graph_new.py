from typing import List, Dict, Tuple
from collections import deque
from graphviz import Digraph

from src.utils import custom_round_float
from src.recipe import Product, Recipe


class FlowEdge():
    """ Represents a flow (edge) on the graph that is moving from one machine to another """
    def __init__(self, product: Product, provide: float, consume: float):
        self.product = product
        self.provide = provide # Numerator
        self.consume = consume # Denominator


# Abstract class
class Vertex():
    """ Represents a vertex on the graph """
    def __init__(self):
        self.src: Dict[Vertex, FlowEdge] = {}
        self.dst: Dict[Vertex, FlowEdge] = {}
        self.indegree = 0
    
    def add_src(self, vertex: 'Vertex', flow: FlowEdge):
        self.src[vertex] = flow
    
    def add_dst(self, vertex: 'Vertex', flow: FlowEdge):
        self.dst[vertex] = flow


class SourceVertex(Vertex):
    """ Represents a source of products where input products are provided """
    def __init__(self, product: Product, rate: float):
        super().__init__()
        self.provide_product = product
        self.provide_rate = rate
    
    # Override with error
    def add_src(self, vertex: 'Vertex', flow: FlowEdge):
        raise ValueError("Source vertex cannot have incoming edges")


class SinkVertex(Vertex):
    """ Represents a sink of products where output products are required """
    def __init__(self, product: Product, rate: float):
        super().__init__()
        self.receive_product = product
        self.receive_rate = rate
    
    # Override with error
    def add_dst(self, vertex: 'Vertex', flow: FlowEdge):
        raise ValueError("Sink vertex cannot have outgoing edges")


class MachineVertex(Vertex):
    """ Represents a machine (vertex) on the graph where production with a recipe is taken place """
    def __init__(self, recipe: Recipe, scale: int):
        super().__init__()
        self.recipe = recipe
        self.scale = scale
    
    def in_demands(self) -> Dict[Product, float]:
        """ Calcute expected in-flows of this machine according to recipe and scale """
        # Scale up each product rate according to scale
        return {product: rate * self.scale for product, rate in self.recipe.inputs.items()}
    
    def out_available(self) -> Dict[Product, float]:
        """ Calcute expected out-flows of this machine according to recipe and scale """
        # Scale up each product rate according to scale
        d = {}
        for product, rate in self.recipe.outputs.items():
            if product in self.recipe.inputs:
                continue
            d[product] = rate * self.scale
        return d
    
    def satisfied(self) -> bool:
        """ Check if the machine's in-flows and out-flows satisfy the recipe demands """
        # Check all demands
        for product, demand in self.in_demands().items():
            # Sum all flows of that product
            total_in_flow = sum(flow.provide for vertex, flow in self.src.items() if flow.product.name == product.name)
            if total_in_flow < demand:
                return False
        return True


class WasteVertex(Vertex):
    """ Represents a sink of products which is wasted """
    def __init__(self, product: Product, rate: float):
        super().__init__()
        self.wasted_product = product
        self.wasted_rate = rate
    
    def add_dst(self, vertex: 'Vertex', flow: FlowEdge):
        raise ValueError("Waste vertex cannot have outgoing edges")


class ProductionGraph():
    """ A graph for whole production routine """
    def __init__(self):
        self.vertices: List[Vertex] = []
        self.edges: List[FlowEdge] = []
    
    def add_vertex(self, vertex: Vertex):
        self.vertices.append(vertex)

    def add_edge(self, edge: FlowEdge):
        self.edges.append(edge)
    
    def create(self, recipe_count_pairs: List[Tuple[Recipe, int]], inputs: Dict[Product, float], outputs: Dict[Product, float]):
        """ Create the production graph from recipes and their scale """
        # Add source vertices
        for product, rate in inputs.items():
            vertex = SourceVertex(product, custom_round_float(rate))
            self.add_vertex(vertex)
            
        # Add sink vertices
        for product, score in outputs.items():
            vertex = SinkVertex(product, 0)
            self.add_vertex(vertex)
            
        # Add machine vertices
        for recipe, scale in recipe_count_pairs:
            if scale == 0:
                continue
            vertex = MachineVertex(recipe, scale)
            self.add_vertex(vertex)
        
        # 
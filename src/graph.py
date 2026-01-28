from typing import List, Dict, Tuple
from collections import deque
from graphviz import Digraph

from src.common import custom_round_float
from src.recipe import Product, Recipe


class FlowEdge:
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
    
    def add_src(self, vertex: 'Vertex', flow: FlowEdge):
        raise ValueError("Source vertex cannot have incoming edges")


class SinkVertex(Vertex):
    """ Represents a sink of products where output products are required """
    def __init__(self, product: Product, rate: float):
        super().__init__()
        self.receive_product = product
        self.receive_rate = rate
    
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
            total_in_flow = sum(flow.provide for vertex, flow in self.src.items() if flow.product == product)
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


class ProductionGraph:
    """ A graph for the whole production line """
    def __init__(self):
        self.vertices: List[Vertex] = []
        self.edges: List[FlowEdge] = []

    def add_vertex(self, vertex: Vertex):
        self.vertices.append(vertex)

    def add_edge(self, edge: FlowEdge):
        self.edges.append(edge)
    
    def create(self, recipe_count_pairs: List[Tuple[Recipe, int]], inputs: Dict[Product, float], outputs: Dict[Product, float]):
        """ Create the production graph from recipes and their scale """
        # Create vertices
        source_vertices: List[SourceVertex] = []
        sink_vertices: List[SinkVertex] = []
        machine_vertices: List[MachineVertex] = []
        
        # Add source vertices
        for product, rate in inputs.items():
            vertex = SourceVertex(product, custom_round_float(rate))
            self.add_vertex(vertex)
            source_vertices.append(vertex)
            
        # Add sink vertices
        for product, score in outputs.items():
            vertex = SinkVertex(product, 0)
            self.add_vertex(vertex)
            sink_vertices.append(vertex)
            
        # Add machine vertices
        for recipe, scale in recipe_count_pairs:
            if scale == 0:
                continue
            vertex = MachineVertex(recipe, scale)
            self.add_vertex(vertex)
            machine_vertices.append(vertex)

        # Precompute fixed production rates from solver
        machine_inputs: Dict[MachineVertex, Dict[Product, float]] = {}
        machine_outputs: Dict[MachineVertex, Dict[Product, float]] = {}
        
        for vertex in machine_vertices:
            machine_inputs[vertex] = {p: rate * vertex.scale for p, rate in vertex.recipe.inputs.items()}
            machine_outputs[vertex] = {p: rate * vertex.scale for p, rate in vertex.recipe.outputs.items() if p not in vertex.recipe.inputs}

        # Global product record
        total_produced: Dict[Product, float] = {}
        total_consumed: Dict[Product, float] = {}
        
        # Calculate totals
        for vertex in machine_vertices:
            for product, amount in machine_outputs[vertex].items():
                total_produced[product] = total_produced.get(product, 0) + amount
            for product, amount in machine_inputs[vertex].items():
                total_consumed[product] = total_consumed.get(product, 0) + amount

        # Step 1: Connect sources to machines
        for src_vertex in source_vertices:
            product = src_vertex.provide_product
            demanding_machines = [v for v in machine_vertices if product in machine_inputs[v]]
            
            if not demanding_machines:
                # No demand - all goes to waste
                waste_vertex = WasteVertex(product, src_vertex.provide_rate)
                self.add_vertex(waste_vertex)
                edge = FlowEdge(product, src_vertex.provide_rate, src_vertex.provide_rate)
                self.add_edge(edge)
                src_vertex.add_dst(waste_vertex, edge)
                waste_vertex.add_src(src_vertex, edge)
                continue
                
            total_demand = sum(machine_inputs[v][product] for v in demanding_machines)
            remaining = src_vertex.provide_rate
            
            for vertex in demanding_machines:
                demand = machine_inputs[vertex][product]
                assign = min(demand, remaining * (demand / total_demand) if total_demand > 0 else 0)
                assign = custom_round_float(assign)
                
                if assign > 0:
                    edge = FlowEdge(product, assign, demand)
                    self.add_edge(edge)
                    src_vertex.add_dst(vertex, edge)
                    vertex.add_src(src_vertex, edge)
                    remaining -= assign
            
            # Waste unused source
            if remaining > 1e-6:
                waste_vertex = WasteVertex(product, custom_round_float(remaining))
                self.add_vertex(waste_vertex)
                edge = FlowEdge(product, custom_round_float(remaining), custom_round_float(remaining))
                self.add_edge(edge)
                src_vertex.add_dst(waste_vertex, edge)
                waste_vertex.add_src(src_vertex, edge)

        # Step 2: Connect machines to machines (intermediate products)
        for producer in machine_vertices:
            for product, amount in machine_outputs[producer].items():
                consuming_machines = [v for v in machine_vertices if product in machine_inputs[v]]
                
                if not consuming_machines:
                    continue  # Will be handled in step 3
                    
                total_demand = sum(machine_inputs[v][product] for v in consuming_machines)
                remaining = amount
                
                for consumer in consuming_machines:
                    demand = machine_inputs[consumer][product]
                    assign = min(demand, remaining * (demand / total_demand) if total_demand > 0 else 0)
                    assign = custom_round_float(assign)
                    
                    if assign > 0:
                        edge = FlowEdge(product, assign, demand)
                        self.add_edge(edge)
                        producer.add_dst(consumer, edge)
                        consumer.add_src(producer, edge)
                        remaining -= assign

        # Step 3: Connect machines to sinks (final outputs)
        for producer in machine_vertices:
            for product, amount in machine_outputs[producer].items():
                if product not in outputs:
                    continue
                    
                # Check how much already consumed by machines
                already_consumed = sum(edge.provide for edge in producer.dst.values() if edge.product == product)
                remaining = amount - already_consumed
                
                if remaining > 1e-6:
                    # Find matching sink
                    sink = next((v for v in sink_vertices if v.receive_product == product), None)
                    if sink:
                        remaining = custom_round_float(remaining)
                        edge = FlowEdge(product, remaining, remaining)
                        self.add_edge(edge)
                        producer.add_dst(sink, edge)
                        sink.add_src(producer, edge)
                        sink.receive_rate += remaining

        # Step 4: Throw remaining products into waste
        for producer in machine_vertices:
            for product, amount in machine_outputs[producer].items():
                already_allocated = sum(edge.provide for edge in producer.dst.values() if edge.product == product)
                remaining = amount - already_allocated
                
                if remaining > 1e-6:
                    waste_vertex = WasteVertex(product, custom_round_float(remaining))
                    self.add_vertex(waste_vertex)
                    edge = FlowEdge(product, custom_round_float(remaining), custom_round_float(remaining))
                    self.add_edge(edge)
                    producer.add_dst(waste_vertex, edge)
                    waste_vertex.add_src(producer, edge)
    
    
    def terminal_display(self):
        """ Display the graph """
        print("\n=== Production Graph ===")
        
        # Display vertices with details
        for i, vertex in enumerate(self.vertices):
            if isinstance(vertex, SourceVertex):
                print(f"[{i}] SOURCE: {vertex.provide_product} (rate: {vertex.provide_rate})")
            elif isinstance(vertex, SinkVertex):
                print(f"[{i}] SINK: {vertex.receive_product} (rate: {vertex.receive_rate})")
            elif isinstance(vertex, MachineVertex):
                print(f"[{i}] MACHINE: {vertex.recipe} (scale: {vertex.scale})")
            elif isinstance(vertex, WasteVertex):
                print(f"[{i}] WASTE: {vertex.wasted_product} (rate: {vertex.wasted_rate})")
            
        print("\n=== Connections ===")
        # Display connections
        for i, vertex in enumerate(self.vertices):
            if vertex.dst:
                for dst_vertex, edge in vertex.dst.items():
                    dst_idx = self.vertices.index(dst_vertex)
                    print(f"[{i}] -> [{dst_idx}]: {edge.product} ({edge.provide}/{edge.consume})")
    
    
    def visualize(self, save_path, title):
        """ Visualize the graph with graphviz """
        # Validate that the graph is created
        if not self.vertices:
            print("No graph created yet. Please call create() first.")
            return
        
        # Create a new directed graph
        dot = Digraph(comment=title)
        dot.attr(label=title, fontsize='24', labelloc='t', fontname='Helvetica-Bold')

        # Add vertices
        for i, vertex in enumerate(self.vertices):
            if isinstance(vertex, SourceVertex):
                dot.node(str(i), f"{vertex.provide_product} (Supplied: {vertex.provide_rate})", color='blue')
            elif isinstance(vertex, SinkVertex):
                dot.node(str(i), f"{vertex.receive_product} (Received: {vertex.receive_rate})", color='green')
            elif isinstance(vertex, MachineVertex):
                dot.node(str(i), f"{vertex.recipe} (Scale: {vertex.scale})", shape="box")
            elif isinstance(vertex, WasteVertex):
                dot.node(str(i), f"{vertex.wasted_product} (Wasted: {vertex.wasted_rate})", color='red')

        # Add edges
        for i, vertex in enumerate(self.vertices):
            if not vertex.dst:
                continue
            for dst_vertex, edge in vertex.dst.items():
                dst_idx = self.vertices.index(dst_vertex)
                color = ''
                # (Highest priority) Color the edge red if the destination is waste
                if isinstance(dst_vertex, WasteVertex):
                    color = 'red'
                # Color the edge green if the destination is sink
                elif isinstance(dst_vertex, SinkVertex):
                    color = 'green'
                # Color the edge blue if the source is source
                elif isinstance(vertex, SourceVertex):
                    color = 'blue'
                # Add the edge with label
                dot.edge(str(i), str(dst_idx), label=f"{edge.product} ({edge.provide}/{edge.consume})", color=color, fontcolor=color)
                
        # Render the graph
        dot.render(save_path, format='png', cleanup=True)
        print(f"Graph visualization saved as {save_path}")
        # dot.view()
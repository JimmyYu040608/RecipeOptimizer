from typing import List, Dict, Tuple
from collections import deque
from graphviz import Digraph

from src.common import round_float_to_2
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
            print(f'product: {product.name}, rate: {rate}, scale: {self.scale}')
            d[product] = rate * self.scale
        return {product: rate * self.scale for product, rate in self.recipe.outputs.items()}
    
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
        self.vertices: List[MachineVertex] = []
        self.edges: List[FlowEdge] = []

    def add_vertex(self, vertex: MachineVertex):
        self.vertices.append(vertex)

    def add_edge(self, edge: FlowEdge):
        self.edges.append(edge)
    
    def create(self, recipe_count_pairs: List[Tuple[Recipe, int]], inputs: Dict[Product, float], outputs: Dict[Product, float]):
        """ Create the production graph from recipes and their scale """
        # Add source vertices
        for product, rate in inputs.items():
            vertex = SourceVertex(product, round_float_to_2(rate))
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

        # Add ingredient edges from sources to machines with pro-rata allocation if needed
        for src_vertex in [v for v in self.vertices if isinstance(v, SourceVertex)]:
            product = src_vertex.provide_product
            demanding_machines = [v for v in self.vertices if isinstance(v, MachineVertex) and product in v.in_demands()]
            total_demand = sum(v.in_demands()[product] for v in demanding_machines)
            alloc_ratio = min(1.0, src_vertex.provide_rate / total_demand) if total_demand > 0 else 1.0
            unused_rate = src_vertex.provide_rate
            for vertex in demanding_machines:
                demand = vertex.in_demands()[product]
                assign = round_float_to_2(demand * alloc_ratio)
                edge = FlowEdge(product, assign, round_float_to_2(demand))
                self.add_edge(edge)
                src_vertex.add_dst(vertex, edge)
                vertex.add_src(src_vertex, edge)
                unused_rate -= assign
            # Record wasted product with WasteVertex
            if unused_rate > 0:
                waste_vertex = WasteVertex(product, round_float_to_2(unused_rate))
                self.add_vertex(waste_vertex)
                waste_edge = FlowEdge(product, round_float_to_2(unused_rate), round_float_to_2(unused_rate))
                self.add_edge(waste_edge)
                src_vertex.add_dst(waste_vertex, waste_edge)
                waste_vertex.add_src(src_vertex, waste_edge)

        # Precompute producers for each product
        producers: Dict[Product, List[MachineVertex]] = {}
        for vertex in [v for v in self.vertices if isinstance(v, MachineVertex)]:
            for product, rate in vertex.recipe.outputs.items():
                if product not in producers:
                    producers[product] = []
                producers[product].append(vertex)

        # Compute indegree for topological sort (number of upstream machine groups for intermediate inputs)
        indegree: Dict[MachineVertex, int] = {}
        for vertex in [v for v in self.vertices if isinstance(v, MachineVertex)]:
            upstream = set()
            for product in vertex.recipe.inputs.keys():
                if product in inputs:
                    continue  # raw input, handled by sources
                if product in producers:
                    upstream.update(producers[product])
            indegree[vertex] = len(upstream)

        # Queue for topological processing
        queue = deque([v for v in self.vertices if isinstance(v, MachineVertex) and indegree.get(v, 0) == 0])

        # Precompute remaining demands
        remaining_demands = {v: v.in_demands().copy() for v in self.vertices if isinstance(v, MachineVertex)}

        while queue:
            current = queue.popleft()

            # Compute provided for each input product
            provided_dict: Dict[Product, float] = {}
            for src_vertex, flow in current.src.items():
                if flow.product not in provided_dict:
                    provided_dict[flow.product] = 0.0
                provided_dict[flow.product] += flow.provide

            # Compute min_ratio
            demands = current.in_demands()
            ratios = []
            for p, d in demands.items():
                prov = provided_dict.get(p, 0.0)
                ratios.append(prov / d if d > 0 else 1.0)
            min_ratio = min(ratios) if ratios else 1.0

            # Adjust input flows for excess (overprovided non-limiting inputs)
            for p, d in demands.items():
                effective_consume = round_float_to_2(d * min_ratio)
                total_provided = provided_dict.get(p, 0.0)
                if total_provided > effective_consume + 1e-6:  # tolerance for float
                    for src_vertex, flow in current.src.items():
                        if flow.product != p:
                            continue
                        share = round_float_to_2((flow.provide / total_provided) * effective_consume if total_provided > 0 else 0.0)
                        excess = round_float_to_2(flow.provide - share)
                        flow.provide = share
                        if excess > 0:
                            waste_vertex = WasteVertex(p, excess)
                            self.add_vertex(waste_vertex)
                            waste_edge = FlowEdge(p, excess, excess)
                            self.add_edge(waste_edge)
                            src_vertex.add_dst(waste_vertex, waste_edge)
                            waste_vertex.add_src(src_vertex, waste_edge)

            # Compute effective out_available
            effective_scale = round_float_to_2(current.scale * min_ratio)
            out_available = {product: round_float_to_2(rate * effective_scale) for product, rate in current.recipe.outputs.items() if product not in current.recipe.inputs}

            unused_products = out_available.copy()

            # Assign outputs
            for product, available in out_available.items():
                # Assign to machines with pro-rata if overdemanded
                demanding_machines = [v for v in self.vertices if isinstance(v, MachineVertex) and product in remaining_demands.get(v, {}) and remaining_demands[v][product] > 0]
                total_rem_demand = sum(remaining_demands[v][product] for v in demanding_machines)
                alloc_ratio = min(1.0, available / total_rem_demand) if total_rem_demand > 0 else 1.0
                for vertex in demanding_machines:
                    rem = remaining_demands[vertex][product]
                    assign = round_float_to_2(rem * alloc_ratio)
                    edge = FlowEdge(product, assign, round_float_to_2(rem))
                    self.add_edge(edge)
                    current.add_dst(vertex, edge)
                    vertex.add_src(current, edge)
                    remaining_demands[vertex][product] -= assign
                    unused_products[product] -= assign

                # Assign to sink if output product and remaining
                remain = unused_products[product]
                if product in outputs and remain > 0:
                    for out_vertex in [v for v in self.vertices if isinstance(v, SinkVertex) and v.receive_product == product]:
                        edge = FlowEdge(product, remain, remain)
                        self.add_edge(edge)
                        current.add_dst(out_vertex, edge)
                        out_vertex.add_src(current, edge)
                        out_vertex.receive_rate += remain
                        unused_products[product] = 0
                        break

            # Record wasted products
            for product, unused_rate in unused_products.items():
                if unused_rate > 0:
                    waste_vertex = WasteVertex(product, round_float_to_2(unused_rate))
                    self.add_vertex(waste_vertex)
                    waste_edge = FlowEdge(product, round_float_to_2(unused_rate), round_float_to_2(unused_rate))
                    self.add_edge(waste_edge)
                    current.add_dst(waste_vertex, waste_edge)
                    waste_vertex.add_src(current, waste_edge)

            # Decrease indegree for unique downstream machines
            unique_dsts = set(dst for dst in current.dst.keys() if isinstance(dst, MachineVertex))
            for dst in unique_dsts:
                indegree[dst] -= 1
                if indegree[dst] == 0:
                    queue.append(dst)
    
    
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
import random
from collections import defaultdict

import networkx as nx
import numpy as np


# ============================================================================
# TOPOLOGY AND DELAY MODELING
# ============================================================================

class PlanarGridTopology:
    """
    Simplified 2D planar grid topology for dynamic-circuit placement studies.
    """
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.num_qubits = width * height
        self.grid = nx.grid_2d_graph(width, height)
        
        self.coord_to_idx = {node: i for i, node in enumerate(self.grid.nodes())}
        self.idx_to_coord = {i: node for i, node in enumerate(self.grid.nodes())}

    def manhattan_distance(self, q1_idx, q2_idx):
        x1, y1 = self.idx_to_coord[q1_idx]
        x2, y2 = self.idx_to_coord[q2_idx]
        return abs(x1 - x2) + abs(y1 - y2)

    def calculate_signal_delay(self, distance):
        """
        Simplified feed-forward delay model:
        base latency + distance-dependent routing penalty
        """
        base_latency_ns = 50.0
        routing_penalty_ns = 15.0
        return base_latency_ns + (distance * routing_penalty_ns)


# ============================================================================
# DYNAMIC DEPENDENCY GENERATORS
# ============================================================================

def generate_random_dynamic_dependencies(num_qubits, num_measurements, min_weight=1, max_weight=3, seed=None):
    """
    Generates random weighted dependencies:
        (measured_qubit, target_qubit, weight)
    """
    if seed is not None:
        random.seed(seed)
    
    dependencies = []
    for _ in range(num_measurements):
        m, t = random.sample(range(num_qubits), 2)
        w = random.randint(min_weight, max_weight)
        dependencies.append((m, t, w))
    return dependencies


def generate_clustered_dynamic_dependencies(
    num_qubits,
    num_clusters=4,
    num_measurements=30,
    local_prob=0.8,
    min_weight=1,
    max_weight=3,
    seed=None
):
    """
    Generates weighted dynamic dependencies with cluster structure.
    Most dependencies are within the same logical cluster.
    """
    if seed is not None:
        random.seed(seed)
    
    clusters = [[] for _ in range(num_clusters)]
    for q in range(num_qubits):
        clusters[q % num_clusters].append(q)
    
    dependencies = []
    for _ in range(num_measurements):
        if random.random() < local_prob:
            cluster = random.choice(clusters)
            if len(cluster) >= 2:
                m, t = random.sample(cluster, 2)
            else:
                m, t = random.sample(range(num_qubits), 2)
        else:
            c1, c2 = random.sample(range(num_clusters), 2)
            m = random.choice(clusters[c1])
            t = random.choice(clusters[c2])
        
        w = random.randint(min_weight, max_weight)
        dependencies.append((m, t, w))
    
    return dependencies


def generate_hub_spoke_dynamic_dependencies(
    num_qubits,
    num_hubs=3,
    num_measurements=30,
    min_weight=1,
    max_weight=4,
    seed=None
):
    """
    Generates weighted dependencies where a few hub qubits frequently feed
    forward to many targets.
    """
    if seed is not None:
        random.seed(seed)
    
    hubs = random.sample(range(num_qubits), num_hubs)
    dependencies = []
    
    for _ in range(num_measurements):
        m = random.choice(hubs)
        t = random.choice([q for q in range(num_qubits) if q != m])
        w = random.randint(min_weight, max_weight)
        dependencies.append((m, t, w))
    
    return dependencies


def generate_conflicting_dynamic_dependencies(
    num_qubits,
    num_clusters=4,
    num_measurements=30,
    min_weight=1,
    max_weight=3,
    seed=None
):
    """
    Generate dynamic dependencies that deliberately conflict with clustered
    quantum structure by favoring cross-cluster measurement-target pairs.
    """
    if seed is not None:
        random.seed(seed)
    
    clusters = [[] for _ in range(num_clusters)]
    for q in range(num_qubits):
        clusters[q % num_clusters].append(q)
    
    dependencies = []
    for _ in range(num_measurements):
        c1, c2 = random.sample(range(num_clusters), 2)
        m = random.choice(clusters[c1])
        t = random.choice(clusters[c2])
        w = random.randint(min_weight, max_weight)
        dependencies.append((m, t, w))
    
    return dependencies


# ============================================================================
# DYNAMIC CIRCUIT DELAY-AWARE PLACEMENT OPTIMIZER
# ============================================================================

class DynamicCircuitRouter:
    """
    Optimizes logical-to-physical qubit placement to reduce modeled classical
    feed-forward delay for dynamic circuit dependencies on a planar grid.
    """
    
    def __init__(self, topology):
        self.topology = topology
    
    def _normalize_dependencies(self, dependencies):
        normalized = []
        for dep in dependencies:
            if len(dep) == 2:
                m, t = dep
                normalized.append((m, t, 1))
            elif len(dep) == 3:
                m, t, w = dep
                normalized.append((m, t, w))
            else:
                raise ValueError("Each dependency must be (m, t) or (m, t, weight)")
        return normalized
    
    def _initial_mapping(self):
        logical_to_physical = {q: q for q in range(self.topology.num_qubits)}
        physical_to_logical = {q: q for q in range(self.topology.num_qubits)}
        return logical_to_physical, physical_to_logical
    
    def calculate_total_delay(self, dependencies, logical_to_physical):
        dependencies = self._normalize_dependencies(dependencies)
        total_delay = 0.0
        
        for measure_q, target_q, weight in dependencies:
            phys_m = logical_to_physical[measure_q]
            phys_t = logical_to_physical[target_q]
            dist = self.topology.manhattan_distance(phys_m, phys_t)
            total_delay += weight * self.topology.calculate_signal_delay(dist)
        
        return total_delay
    
    def delta_cost_for_swap(self, dependencies_by_qubit, logical_to_physical, q1, q2):
        """
        Compute cost change if logical qubits q1 and q2 swap physical positions.
        Only dependencies touching q1 or q2 are affected.
        """
        if q1 == q2:
            return 0.0
        
        p1 = logical_to_physical[q1]
        p2 = logical_to_physical[q2]
        affected_dependencies = dependencies_by_qubit[q1] | dependencies_by_qubit[q2]
        delta = 0.0
        
        for dep in affected_dependencies:
            m, t, w = dep
            
            old_pm = logical_to_physical[m]
            old_pt = logical_to_physical[t]
            old_dist = self.topology.manhattan_distance(old_pm, old_pt)
            old_cost = w * self.topology.calculate_signal_delay(old_dist)
            
            new_pm = p2 if m == q1 else p1 if m == q2 else old_pm
            new_pt = p2 if t == q1 else p1 if t == q2 else old_pt
            new_dist = self.topology.manhattan_distance(new_pm, new_pt)
            new_cost = w * self.topology.calculate_signal_delay(new_dist)
            
            delta += (new_cost - old_cost)
        
        return delta
    
    def optimize_placement(self, dependencies, max_iterations=3000, initial_temp=100.0, cooling_rate=0.995):
        """
        Simulated annealing over logical-qubit swaps.
        Returns:
            best_mapping, best_cost
        """
        dependencies = self._normalize_dependencies(dependencies)
        logical_to_physical, physical_to_logical = self._initial_mapping()
        
        dependencies_by_qubit = defaultdict(set)
        for dep in dependencies:
            m, t, w = dep
            dependencies_by_qubit[m].add(dep)
            dependencies_by_qubit[t].add(dep)
        
        current_cost = self.calculate_total_delay(dependencies, logical_to_physical)
        best_cost = current_cost
        best_mapping = dict(logical_to_physical)
        
        temp = initial_temp
        logical_qubits = list(range(self.topology.num_qubits))
        
        for _ in range(max_iterations):
            q1, q2 = random.sample(logical_qubits, 2)
            delta = self.delta_cost_for_swap(dependencies_by_qubit, logical_to_physical, q1, q2)
            new_cost = current_cost + delta
            
            if delta < 0 or random.random() < np.exp(-delta / temp):
                p1 = logical_to_physical[q1]
                p2 = logical_to_physical[q2]
                
                logical_to_physical[q1], logical_to_physical[q2] = p2, p1
                physical_to_logical[p1], physical_to_logical[p2] = q2, q1
                current_cost = new_cost
                
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_mapping = dict(logical_to_physical)
            
            temp *= cooling_rate
            if temp < 1e-6:
                break
        
        return best_mapping, best_cost


# ============================================================================
# HYBRID WORKLOAD GENERATION
# ============================================================================

def generate_quantum_interaction_graph(
    num_qubits,
    num_clusters=4,
    num_interactions=120,
    local_prob=0.8,
    min_weight=1,
    max_weight=3,
    seed=None
):
    """
    Generate a weighted quantum interaction graph with clustered structure.
    """
    if seed is not None:
        random.seed(seed)
    
    G = nx.Graph()
    G.add_nodes_from(range(num_qubits))
    
    clusters = [[] for _ in range(num_clusters)]
    for q in range(num_qubits):
        clusters[q % num_clusters].append(q)
    
    for _ in range(num_interactions):
        if random.random() < local_prob:
            cluster = random.choice(clusters)
            if len(cluster) >= 2:
                q1, q2 = random.sample(cluster, 2)
            else:
                q1, q2 = random.sample(range(num_qubits), 2)
        else:
            c1, c2 = random.sample(range(num_clusters), 2)
            q1 = random.choice(clusters[c1])
            q2 = random.choice(clusters[c2])
        
        w = random.randint(min_weight, max_weight)
        
        if G.has_edge(q1, q2):
            G[q1][q2]["weight"] += w
        else:
            G.add_edge(q1, q2, weight=w)
    
    return G


def generate_hybrid_workload(
    num_qubits,
    quantum_clusters=4,
    quantum_interactions=120,
    dynamic_mode="clustered",
    dynamic_measurements=30,
    seed=None
):
    """
    Generate both:
    - a weighted quantum interaction graph
    - a weighted dynamic dependency list
    """
    interaction_graph = generate_quantum_interaction_graph(
        num_qubits=num_qubits,
        num_clusters=quantum_clusters,
        num_interactions=quantum_interactions,
        seed=seed
    )
    
    if dynamic_mode == "clustered":
        dynamic_dependencies = generate_clustered_dynamic_dependencies(
            num_qubits=num_qubits,
            num_clusters=quantum_clusters,
            num_measurements=dynamic_measurements,
            local_prob=0.8,
            seed=seed
        )
    elif dynamic_mode == "hub_spoke":
        dynamic_dependencies = generate_hub_spoke_dynamic_dependencies(
            num_qubits=num_qubits,
            num_hubs=3,
            num_measurements=dynamic_measurements,
            seed=seed
        )
    elif dynamic_mode == "random":
        dynamic_dependencies = generate_random_dynamic_dependencies(
            num_qubits=num_qubits,
            num_measurements=dynamic_measurements,
            seed=seed
        )
    elif dynamic_mode == "conflicting":
        dynamic_dependencies = generate_conflicting_dynamic_dependencies(
            num_qubits=num_qubits,
            num_clusters=quantum_clusters,
            num_measurements=dynamic_measurements,
            seed=seed
        )
    else:
        raise ValueError("dynamic_mode must be one of: clustered, hub_spoke, random, conflicting")
    
    return interaction_graph, dynamic_dependencies


# ============================================================================
# HYBRID COST MODEL
# ============================================================================

class HybridPlacementCostModel:
    """
    Combined objective:
        alpha * quantum communication cost
      + beta  * dynamic feed-forward delay cost
    """
    
    def __init__(self, topology, alpha=1.0, beta=1.0):
        self.topology = topology
        self.alpha = alpha
        self.beta = beta
    
    def quantum_cost(self, interaction_graph, logical_to_physical):
        total = 0.0
        for q1, q2, data in interaction_graph.edges(data=True):
            w = data.get("weight", 1)
            p1 = logical_to_physical[q1]
            p2 = logical_to_physical[q2]
            dist = self.topology.manhattan_distance(p1, p2)
            total += w * dist
        return total
    
    def dynamic_cost(self, dynamic_dependencies, logical_to_physical):
        total = 0.0
        for m, t, w in dynamic_dependencies:
            pm = logical_to_physical[m]
            pt = logical_to_physical[t]
            dist = self.topology.manhattan_distance(pm, pt)
            total += w * self.topology.calculate_signal_delay(dist)
        return total
    
    def total_cost(self, interaction_graph, dynamic_dependencies, logical_to_physical):
        q_cost = self.quantum_cost(interaction_graph, logical_to_physical)
        d_cost = self.dynamic_cost(dynamic_dependencies, logical_to_physical)
        return self.alpha * q_cost + self.beta * d_cost
    
    def evaluate(self, interaction_graph, dynamic_dependencies, logical_to_physical):
        q_cost = self.quantum_cost(interaction_graph, logical_to_physical)
        d_cost = self.dynamic_cost(dynamic_dependencies, logical_to_physical)
        total = self.alpha * q_cost + self.beta * d_cost
        
        return {
            "quantum_cost": q_cost,
            "dynamic_cost": d_cost,
            "total_cost": total,
        }


# ============================================================================
# HYBRID PLACEMENT OPTIMIZER
# ============================================================================

class HybridPlacementOptimizer:
    """
    Simulated annealing optimizer for combined quantum + dynamic placement cost.
    """
    
    def __init__(self, topology, cost_model):
        self.topology = topology
        self.cost_model = cost_model
    
    def _initial_mapping(self):
        logical_to_physical = {q: q for q in range(self.topology.num_qubits)}
        physical_to_logical = {q: q for q in range(self.topology.num_qubits)}
        return logical_to_physical, physical_to_logical
    
    def _build_quantum_dependencies_by_qubit(self, interaction_graph):
        by_qubit = defaultdict(set)
        for q1, q2, data in interaction_graph.edges(data=True):
            weight = data.get("weight", 1)
            edge = (q1, q2, weight)
            by_qubit[q1].add(edge)
            by_qubit[q2].add(edge)
        return by_qubit
    
    def _build_dynamic_dependencies_by_qubit(self, dynamic_dependencies):
        by_qubit = defaultdict(set)
        for dep in dynamic_dependencies:
            m, t, w = dep
            by_qubit[m].add(dep)
            by_qubit[t].add(dep)
        return by_qubit
    
    def delta_cost_for_swap(
        self,
        interaction_graph,
        dynamic_dependencies,
        quantum_by_qubit,
        dynamic_by_qubit,
        logical_to_physical,
        q1,
        q2
    ):
        if q1 == q2:
            return 0.0
        
        p1 = logical_to_physical[q1]
        p2 = logical_to_physical[q2]
        delta = 0.0
        
        affected_quantum = quantum_by_qubit[q1] | quantum_by_qubit[q2]
        for edge in affected_quantum:
            a, b, w = edge
            
            old_pa = logical_to_physical[a]
            old_pb = logical_to_physical[b]
            old_cost = self.cost_model.alpha * w * self.topology.manhattan_distance(old_pa, old_pb)
            
            new_pa = p2 if a == q1 else p1 if a == q2 else old_pa
            new_pb = p2 if b == q1 else p1 if b == q2 else old_pb
            new_cost = self.cost_model.alpha * w * self.topology.manhattan_distance(new_pa, new_pb)
            
            delta += (new_cost - old_cost)
        
        affected_dynamic = dynamic_by_qubit[q1] | dynamic_by_qubit[q2]
        for dep in affected_dynamic:
            m, t, w = dep
            
            old_pm = logical_to_physical[m]
            old_pt = logical_to_physical[t]
            old_cost = self.cost_model.beta * w * self.topology.calculate_signal_delay(
                self.topology.manhattan_distance(old_pm, old_pt)
            )
            
            new_pm = p2 if m == q1 else p1 if m == q2 else old_pm
            new_pt = p2 if t == q1 else p1 if t == q2 else old_pt
            new_cost = self.cost_model.beta * w * self.topology.calculate_signal_delay(
                self.topology.manhattan_distance(new_pm, new_pt)
            )
            
            delta += (new_cost - old_cost)
        
        return delta
    
    def optimize(
        self,
        interaction_graph,
        dynamic_dependencies,
        max_iterations=4000,
        initial_temp=100.0,
        cooling_rate=0.995
    ):
        logical_to_physical, physical_to_logical = self._initial_mapping()
        
        quantum_by_qubit = self._build_quantum_dependencies_by_qubit(interaction_graph)
        dynamic_by_qubit = self._build_dynamic_dependencies_by_qubit(dynamic_dependencies)
        
        current_cost = self.cost_model.total_cost(
            interaction_graph, dynamic_dependencies, logical_to_physical
        )
        best_cost = current_cost
        best_mapping = dict(logical_to_physical)
        
        temp = initial_temp
        logical_qubits = list(range(self.topology.num_qubits))
        
        for _ in range(max_iterations):
            q1, q2 = random.sample(logical_qubits, 2)
            
            delta = self.delta_cost_for_swap(
                interaction_graph,
                dynamic_dependencies,
                quantum_by_qubit,
                dynamic_by_qubit,
                logical_to_physical,
                q1,
                q2
            )
            
            new_cost = current_cost + delta
            
            if delta < 0 or random.random() < np.exp(-delta / temp):
                p1 = logical_to_physical[q1]
                p2 = logical_to_physical[q2]
                
                logical_to_physical[q1], logical_to_physical[q2] = p2, p1
                physical_to_logical[p1], physical_to_logical[p2] = q2, q1
                current_cost = new_cost
                
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_mapping = dict(logical_to_physical)
            
            temp *= cooling_rate
            if temp < 1e-6:
                break
        
        return best_mapping, best_cost

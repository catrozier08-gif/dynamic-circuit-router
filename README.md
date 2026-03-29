# Dynamic Circuit Delay-Aware Placement Optimizer

A prototype hardware-aware placement optimizer for dynamic quantum circuits that minimizes modeled classical feed-forward delay and explores hybrid placement objectives combining quantum locality and dynamic dependency locality.

## Overview

Dynamic quantum circuits introduce placement challenges beyond ordinary two-qubit interaction locality. When a qubit is measured mid-circuit and its result is used to condition a later operation, the measurement outcome must be communicated through the control stack to the target qubit's control path.

If the measured qubit and conditional target are physically distant, this can increase feed-forward delay and extend the target qubit's idle time. This project explores whether placement optimization can reduce that modeled delay on planar hardware layouts.

In addition to dynamic dependency-aware placement, the repository also includes a hybrid objective framework for studying tradeoffs between:

- quantum interaction locality
- dynamic feed-forward locality

## Current capabilities

- 2D planar-grid hardware model
- weighted dynamic dependency generation
- structured synthetic dynamic workloads:
  - clustered
  - hub-spoke
  - explicitly conflicting
  - random
- simulated annealing placement optimization
- modeled feed-forward delay evaluation
- hybrid objective benchmarking with combined quantum and dynamic costs

## Delay model

The current prototype uses a simplified planar-grid delay model:

- qubits occupy positions on a 2D grid
- distance is approximated using Manhattan distance
- feed-forward latency is modeled as a base delay plus a distance-dependent routing penalty
- dynamic dependencies are represented as weighted `(measured_qubit, target_qubit, weight)` tuples

## Hybrid objective

The repository also supports a hybrid placement objective of the form:

`alpha * quantum_cost + beta * dynamic_delay_cost`

This allows experiments on workloads where quantum interaction locality and dynamic feed-forward locality may be aligned, partially conflicting, or explicitly opposed.

## Benchmark highlights

### Dynamic-only placement

On synthetic 10x10 planar benchmarks with weighted dynamic dependencies, the delay-aware placement optimizer reduced modeled feed-forward delay by roughly **48–50%** relative to naive placement across clustered, hub-spoke, and random dependency structures.

### Hybrid placement

Hybrid placement was most beneficial when quantum locality and dynamic feed-forward locality were in tension:

- **clustered workloads:** hybrid gains were small at low dynamic weighting, but grew as dynamic cost became more important
- **hub-spoke workloads:** hybrid optimization significantly outperformed quantum-only placement as dynamic weighting increased
- **explicitly conflicting workloads:** hybrid optimization consistently outperformed both quantum-only and dynamic-only placement under the combined objective

## Important note

This is a **prototype placement and benchmarking tool**, not a hardware-exact control-stack or transpiler implementation.

It does **not** currently:

- extract dependencies from full real-world dynamic-circuit control flow
- synthesize hardware-native feed-forward operations
- perform timing-accurate scheduling
- claim executable hardware decomposition

The current models are intended for comparative optimization studies, not hardware execution claims.

## Quick start

```python
from dynamic_placement_optimizer import (
    PlanarGridTopology,
    DynamicCircuitRouter,
    generate_clustered_dynamic_dependencies,
)

topology = PlanarGridTopology(width=10, height=10)
router = DynamicCircuitRouter(topology)

dependencies = generate_clustered_dynamic_dependencies(
    num_qubits=topology.num_qubits,
    num_clusters=4,
    num_measurements=30,
    seed=42,
)

best_mapping, best_cost = router.optimize_placement(dependencies)

print("Optimized modeled delay:", best_cost)

Example script
You can also run the included example:

python example_usage.py

Suggested use
This repository is most useful as a prototype environment for exploring:

dynamic dependency-aware placement
feed-forward delay minimization
hybrid quantum/dynamic placement objectives
synthetic benchmark construction for dynamic-circuit compilation research


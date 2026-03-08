# Dynamic Circuit Routing Optimizer

A physical placement optimizer designed to minimize classical signal delay and qubit decoherence during Dynamic Circuits (mid-circuit measurements and conditional feed-forward operations).

## The Problem: Classical Routing Delay
In scaling planar quantum architectures (e.g., Heavy-Hex), executing a dynamic circuit requires a classical signal to travel from the measured qubit's control electronics to the target qubit's control electronics. 

If Qubit A (measured) and Qubit B (conditional target) are physically distant on the chip, the classical routing delay increases based on the Manhattan distance. During this delay, Qubit B must sit idle, accumulating phase errors and decoherence. Naive logical-to-physical qubit mapping ignores this classical routing penalty.

## The Solution
This tool uses **Simulated Annealing** to solve the NP-Hard placement problem. It analyzes the dependency graph of mid-circuit measurements and reorganizes the physical qubit layout to minimize the Manhattan distance between dependent pairs, effectively cutting the idle-time decoherence penalty in half.

## Performance
Tested on a 100-qubit (10x10) planar array with 30 random mid-circuit measurement triggers.

```text
2. BEFORE Optimization (Naive Layout):
   - Total routing delay penalty: 4365.0 ns
   - Average delay per measurement: 145.5 ns

3. AFTER Optimization (Simulated Annealing):
   - Total routing delay penalty: 2160.0 ns
   - Average delay per measurement: 72.0 ns

4. Results:
   - Idle-time / Delay Reduction: 50.5%

By minimizing the Manhattan distance between classical condition paths, qubit decoherence during mid-circuit measurements is massively reduced.

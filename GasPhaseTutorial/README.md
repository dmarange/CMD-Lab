# 1. Introduction

## Tutorial Objective

This tutorial is for building a gas-phase workflow that will:

1. Make gas-phase `molecule.traj` files for each molecule.
2. Run a single workflow that performs geometry optimization first and then the vibrational / thermochemistry step in the same directory.
3. Collect DFT energy, ZPE, entropy, thermal correction, and Gibbs free energy results.
4. Collect and analyze results.
5. Tabulate all final data.

## Molecule List

| Molecule | `molecule.traj` built | Combined job run | `final.energy` checked | Results collected |
| --- | --- | --- | --- | --- |
| `NO(g)` |  |  |  |  |
| `H2(g)` |  |  |  |  |
| `H2O(g)` |  |  |  |  |
| `CO2(g)` |  |  |  |  |
| `HNO2(g)` |  |  |  |  |
| `NO2(g)` |  |  |  |  |
| `CO(g)` |  |  |  |  |
| `HNO3(g)` |  |  |  |  |

## Notes

- Add any tutorial-specific assumptions here.
- Record software versions, paths, and method choices here.
- The main workflow now runs from one script in one working directory per molecule.
- Update the table above as each molecule progresses.

## Try The Example
[CO2 Example](GasPhaseTutorial/ExampleSetup/README.md)

## Next Section

[2. Cluster Setup](2.md)

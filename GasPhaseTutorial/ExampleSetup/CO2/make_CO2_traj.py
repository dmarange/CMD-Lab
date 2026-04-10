#!/usr/bin/env python
from ase.build import molecule
from ase.io import write

atoms = molecule("CO2")
atoms.center(vacuum=12.0)
atoms.pbc = True

write("co2.traj", atoms)
print("Wrote co2.traj")
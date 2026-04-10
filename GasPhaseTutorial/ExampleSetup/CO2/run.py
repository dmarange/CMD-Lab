#!/usr/bin/env python
import os, sys
import numpy as np
import matplotlib.pyplot as plt
from math import sqrt, floor, ceil, log, pi, atan
from ase import Atoms, Atom
from ase.io import read, write, Trajectory
from ase.visualize import view
from ase.constraints import FixAtoms, Hookean
from ase.optimize import QuasiNewton, BFGS, BFGSLineSearch
from ase.data import covalent_radii, atomic_numbers
from ase.build import bulk, fcc111, fcc100, add_adsorbate
from ase.spacegroup import crystal
from ase.calculators.vasp import Vasp
from math import *
from math import sqrt
from pathlib import Path
from ase.build import molecule
from ase.units import invcm
from ase.thermochemistry import IdealGasThermo
import re

T = 300.0
P = 101325.0
FREQUENCY_CUTOFF_CM = 20.0

# Update these for each molecule before running!
GEOMETRY = "nonlinear"
SYMMETRY_NUMBER = 1
SPIN = 0
#------------------------------------------------

vasp_path = os.environ.get("EBROOTVASP")
if not isinstance(vasp_path, str):
    raise SystemExit("ERROR: EBROOTVASP not set.")

os.environ["VASP_COMMAND"] = f"srun {vasp_path}/bin/vasp_std"
os.environ["ASE_VASP_COMMAND"] = os.environ["VASP_COMMAND"]

# --------------------------------------------------
# 1. Add gas-phase molecule
# --------------------------------------------------
atoms = read("co2.traj") # Change this to the molecule you want to run (i.e NO2, H2O, etc.)
atoms.center()
atoms.pbc = True

# --------------------------------------------------
# 2. Geometry optimization
# --------------------------------------------------
vasp_geom = Vasp(
    encut=550,
    potim=0.2,
    sigma=0.05,
    ediff=1e-8,
    ediffg=-5e-3,
    algo="Normal",
    gga="PE",
    prec="Accurate",
    ibrion=2,
    isif=2,
    ismear=0,
    ispin=1,
    istart=0,
    isym=0,
    nsw=300,
    ivdw=0,
    ncore=8,
    lcharg=False,
    lwave=False,
    lreal=False,
    kpts=[1, 1, 1],
)

atoms.calc = vasp_geom
e_dft = atoms.get_potential_energy()

with open("dft.energy", "w") as handle:
    handle.write(f"DFT Energy of Geometry Relaxed Molecule: {e_dft}\n")

write("relaxed.traj", atoms)
print(f"DFT Energy of Geometry Relaxed Molecule: {e_dft:.6f} eV")

# --------------------------------------------------
# 3. Vibrational frequency calculation
# --------------------------------------------------
atoms = read("CONTCAR")
atoms.pbc = True

nfree_val = 2
nsw_required = 2 * nfree_val * 3 * len(atoms) + 20

vasp_vib = Vasp(
    encut=550,
    potim=0.015,
    sigma=0.05,
    ediff=1e-8,
    algo="Normal",
    gga="PE",
    prec="Accurate",
    ibrion=5,
    ismear=0,
    ispin=1,
    isym=0,
    nfree=nfree_val,
    nsw=nsw_required,
    ivdw=0,
    ncore=8,
    lcharg=False,
    lwave=False,
    lreal=False,
    kpts=[1, 1, 1],
)

atoms.calc = vasp_vib

# --------------------------------------------------
# 4. Extract vibrational frequencies from OUTCAR
# --------------------------------------------------
real_freqs_cm = []
imag_freqs_cm = []

real_pattern = re.compile(r"^\s*\d+\s+f\s*=.*?([\d.]+)\s*cm-1")
imag_pattern = re.compile(r"^\s*\d+\s+f/i\s*=.*?([\d.]+)\s*cm-1")

with open("OUTCAR", "r") as outcar:
    for line in outcar:
        real_match = real_pattern.match(line)
        imag_match = imag_pattern.match(line)
        if real_match:
            real_freqs_cm.append(float(real_match.group(1)))
        elif imag_match:
            imag_freqs_cm.append(float(imag_match.group(1)))

if not real_freqs_cm and not imag_freqs_cm:
    raise SystemExit("ERROR: No vibrational frequencies found in OUTCAR.")

filtered_freqs_cm = [freq for freq in real_freqs_cm if freq > FREQUENCY_CUTOFF_CM]
vib_energies = [freq * invcm for freq in filtered_freqs_cm]

if not vib_energies:
    raise SystemExit("ERROR: No real frequencies above cutoff were found for thermochemistry.")

# --------------------------------------------------
# 5. Ideal gas thermochemistry
# --------------------------------------------------
thermo = IdealGasThermo(
    vib_energies=vib_energies,
    geometry=GEOMETRY,
    atoms=atoms,
    symmetrynumber=SYMMETRY_NUMBER,
    spin=SPIN,
)

zpe = thermo.get_ZPE_correction()
enthalpy = thermo.get_enthalpy(T, verbose=False)
entropy = thermo.get_entropy(T, P, verbose=False)
thermal_correction = enthalpy - T * entropy
gibbs_free_energy = e_dft + thermal_correction

# --------------------------------------------------
# 6. Output
# --------------------------------------------------
with open("final.energy", "w") as out:
    out.write(f"DFT Energy (eV): {e_dft:.6f}\n")
    out.write(f"Geometry setting: {GEOMETRY}\n")
    out.write(f"Symmetry number: {SYMMETRY_NUMBER}\n")
    out.write(f"Spin: {SPIN}\n")
    out.write(f"Real frequencies found: {len(real_freqs_cm)}\n")
    out.write(f"Frequencies used (> {FREQUENCY_CUTOFF_CM:.1f} cm-1): {len(filtered_freqs_cm)}\n")
    out.write("\n---- Frequencies Used ----\n")
    for i, freq in enumerate(filtered_freqs_cm, start=1):
        out.write(f"Mode {i:3d}: {freq:10.4f} cm-1\n")
    if imag_freqs_cm:
        out.write("\n---- Imaginary Frequencies Discarded ----\n")
        for freq in imag_freqs_cm:
            out.write(f"{freq:10.4f} cm-1\n")
    out.write(f"\nZPE (eV): {zpe:.6f}\n")
    out.write(f"Entropy (eV/K): {entropy:.6e}\n")
    out.write(f"Enthalpy (eV): {enthalpy:.6f}\n")
    out.write(f"Thermal correction H-TS (eV): {thermal_correction:.6f}\n")
    out.write(f"Gibbs Free Energy (eV): {gibbs_free_energy:.6f}\n")

print(f"Real frequencies found: {len(real_freqs_cm)}")
print(f"Frequencies used (> {FREQUENCY_CUTOFF_CM:.1f} cm-1): {len(filtered_freqs_cm)}")
print(f"ZPE: {zpe:.6f} eV")
print(f"Entropy: {entropy:.6e} eV/K")
print(f"Thermal correction H-TS: {thermal_correction:.6f} eV")
print(f"Gibbs Free Energy: {gibbs_free_energy:.6f} eV")
print("Results written to final.energy")

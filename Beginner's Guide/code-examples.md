# Code Examples

## QE - script_maker.py
```python
#!/usr/bin/env python
from math import *
import os,sys
from ase import Atoms
from ase import *
import numpy as np
from ase.data import reference_states as _refstate
from ase.parallel import paropen
from math import *
from ase.constraints import FixAtoms
from ase.optimize import QuasiNewton
from ase.io import *
from ase.lattice.cubic import SimpleCubicFactory
from ase.visualize import view
from ase import*
from ase import lattice
import numpy as np
from ase.lattice.compounds import L1_2
from ase.io.trajectory import PickleTrajectory
from ase.constraints import FixAtoms
from ase.optimize import QuasiNewton
from ase.lattice.surface import add_adsorbate
from numpy import sqrt, pi
from numpy import arctan as atan
from ase import Atoms, Atom
from ase import io
from ase.constraints import FixAtoms
from ase.optimize import QuasiNewton
from ase.data import covalent_radii, atomic_numbers
```
sys.path.append('/home/YOUR_ACCOUNT_NAME/projects/YOURNAME_SUPERVISOR_ACCOUNT_NAME/YOUR_ACCOUNT_NAME/script_maker/module_source')
```python
from inputmaker import PWscfInput

##################
# Slab ###########
##################

functional = 'PBE'
```
mykpts = list([4,4,1])
k = mykpts
ryd=13.605698066
pw=550/ryd
dw=5500/ryd
```
atoms = io.read('initial.traj')
##################
# Adsorbate ######
##################

def add_adsorbate():
    """Adds the adsorbate to the slab."""
    for atom in ads:
        atoms.append(atom)

# Build the adsorbate
```
s_CO = 1.43 # A, C-O bond length
s_OH = 0.94 # A, O-H bond length
d_CO = 1.217 # A, C=O bond length
s_CH = 1.1 # A, C-H bond length
```
ads = Atoms([Atom('H', [0.,0.,0.,], tag=2)])
#gapx = atoms[2].x/2.
#gapy = (atoms[0].y-atoms[4].y)
```
write('slab.traj', atoms)
```
slab=read('slab.traj')

#$$$$$$$$$$$$$$$$$$$$$$$$
```
pwscf = PWscfInput (slab)
mol = slab.get_chemical_symbols()
elements = sorted(set(mol))#,key=list1.index)
spinstatus = False
```
magmoms = {'Co':5,'Cr':5,'Fe':5,'Mn':5,'Mo':5,'Ni':5,'V':5,'W':5}
```
n_spin = 1
```python
for i in range(0,len(elements)):
    if( elements[i] in  ['Co','Cr','Fe','Mn','Mo','Ni','V','W'] ):
        spinstatus = True
        pwscf.system.occupations.degauss = 0.01
        pwscf.electrons.mixing_mode = 'local-TF'
        pwscf.electrons.mixing_beta = 0.1
if spinstatus:
    n_spin = 2
    for i in range(0,len(elements)):
        if( elements[i] in  ['Co','Cr','Fe','Mn','Mo','Ni','V','W'] ):
            pwscf.starting_magnetization.starting_magnetization[i]=magmoms[elements[i]]#slab.get_chemical_symbols()[i]]
        else:
            pwscf.starting_magnetization.starting_magnetization[i]= 0
```
pwscf.system.spin_pol.nspin = n_spin
pwscf.system.occupations.input_dft = functional
```python
for i in range(0,len(elements)):
    pwscf.atomic_species.pseudo_potential[i] = elements[i]+'.UPF'
    pwscf.control.settings.pseudo_dir = '/home/YOUR_ACCOUNT_NAME/projects/YOURNAME_SUPERVISOR_ACCOUNT_NAME/YOUR_ACCOUNT_NAME/pseudo_dir/SSSP_acc_PBE'
```
pwscf.system.occupations.degauss = 0.01
pwscf.electrons.mixing_mode = 'local-TF'
pwscf.electrons.mixing_beta = 0.1
pwscf.control.settings.prefix = 'try'
```bash
#pwscf.control.settings.restart_mode = 'restart'
```
pwscf.control.settings.restart_mode = 'from_scratch'
pwscf.control.settings.calculation= 'relax'
pwscf.system.ecut.ecutwfc= pw
pwscf.system.ecut.ecutrho= dw
pwscf.kpoints.nk = mykpts#[ k/2 , k , 1]
pwscf.kpoints.sk = [ 0 , 0 , 0]
pwscf.write_input ( 'input.in' )
```bash
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$
```
## QE - job.sh
```bash
#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=32
#SBATCH --mem=0
#SBATCH --time=30:00:00           # DD-HH:MM
#SBATCH --mail-user=YOUR_EMAIL
#SBATCH --mail-type=BEGIN,END,TIME_LIMIT,TIME_LIMIT_90,FAIL

#module load  StdEnv/2020  gcc/9.3.0  openmpi/4.0.3
module load  StdEnv/2020  intel/2020.1.217  openmpi/4.0.3
module load quantumespresso/7.2

srun pw.x < input.in > output.out
# --------------------------------------------------------------------------------------------
#/cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcc12/openmpi/4.1.5/bin/mpirun  /home/karamad/software/python/qe/qe-7.3/bin/pw.x < scf.in > output.log

#/cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcc12/openmpi/4.1.5/bin/mpirun  /home/karamad/software/python/qe/qe-7.3/bin/pw.x < input.in > output.log
```
## VASP - job.py
```python
import os
from math import floor, ceil, sqrt, log
import numpy as np
from ase.io import read
from ase.calculators.vasp import Vasp
from pathlib import Path
from ase.io import write

# Check if VASP path is set correctly, if not, exit early
vasp_path = os.environ.get('EBROOTVASP')
if not isinstance(vasp_path, str):
    exit()

# Manually set ASE's VASP command using the loaded module path
```
os.environ["VASP_COMMAND"] = f"mpirun {vasp_path}/bin/vasp_std"
os.environ["ASE_VASP_COMMAND"] = os.environ["VASP_COMMAND"]

```bash
# Get number of cores and calculate NPAR
num_cores = int(os.environ.get('SLURM_NTASKS', '32'))
```
ncore_setting = 4 if num_cores % 4 == 0 else 8

```bash
# Load the slab structure
cu_slab = read('yourstructure.traj')

# Set up the VASP calculator with restart options
```
calc = Vasp(
```
    algo='Fast',
    prec='Accurate',
    xc='PBE',
    encut=550,
    kpts=[3, 3, 1],
    ispin=2,
    ibrion=2,
    nsw=500,
    ismear=1,
    sigma=0.2,
    potim=0.5,
    isif=2,
    ediff=1e-5,
    ediffg=-0.02,
    isym=0,
    istart=0,
    ncore=ncore_setting,
    ivdw=12,
    lwave = True,
    lreal = 'Auto',
    lcharg = True
```
)

```bash
# Attach calculator
```
cu_slab.calc = calc

```bash
# Run VASP (relaxation is internal)
```
final_energy = cu_slab.get_potential_energy()
print(f"Final relaxed energy: {final_energy:.2f} eV")

```bash
# Save final structure\
```
write('yourstructure-relax.traj', cu_slab)

```bash
# Save final energy to file
with Path("final.e").open("w", encoding="utf-8") as f:
    f.write(f"Final Energy: {final_energy:.2f} eV")
```
## VASPSol - job.py
```python
import os
from math import floor, ceil, sqrt, log
import numpy as np
from ase.io import read
from ase.calculators.vasp import Vasp
from pathlib import Path
from ase.io import write

# Check if VASP path is set correctly, if not, exit early
vasp_path = os.environ.get('EBROOTVASP')
if not isinstance(vasp_path, str):
    exit()

# Manually set ASE's VASP command using the loaded module path
```
os.environ["VASP_COMMAND"] = f"mpirun {vasp_path}/bin/vasp_std"
os.environ["ASE_VASP_COMMAND"] = os.environ["VASP_COMMAND"]

```bash
# Get number of cores and calculate NPAR
num_cores = int(os.environ.get('SLURM_NTASKS', '32'))
```
ncore_setting = 4 if num_cores % 4 == 0 else 8

```bash
#Setting different potentials
```
NELECT0 = 401.0000 #from regular VASP run
nelect_value = NELECT0 - 0.5 #Change the NELECT value depending on potential shift

```bash
# Load the slab structure
cu_slab = read('yourstructure.traj')

# Set up the VASP calculator with restart options
```
calc = Vasp(
```
    algo='Fast',
    prec='Accurate',
    xc='PBE',
    encut=550,
    kpts=[3, 3, 1],
    ispin=2,
    ibrion=2,
    nsw=500,
    ismear=1,
    sigma=0.3,
    potim=0.5,
    isif=2,
    ediff=1e-5,
    ediffg=-0.02,
    isym=0,
    istart=0,
    ncore=ncore_setting,
    nelect=nelect_value,
    ivdw=12,
    lwave = True,
    lreal = 'Auto',
    lcharg = True,

    # VASPsol parameters:
    lsol=True, # Turns on implicit solvent
    eb_k=78.4, # Dielectric constant for water at room temp
    ldipol=False, # Dipole correction
    idipol=3, # Dipole along z-axis (surface normal)
    lambda_d_k=3.0,
```
)

```bash
# Attach calculator
```
cu_slab.calc = calc

```bash
# Run VASP (relaxation is internal)
```
final_energy = cu_slab.get_potential_energy()
print(f"Final relaxed energy: {final_energy:.2f} eV")

```bash
# Save final structure
```
write('yourstructureSOl-relax.traj', cu_slab)

```bash
# Save final energy to file
with Path("final.e").open("w", encoding="utf-8") as f:
    f.write(f"Final Energy: {final_energy:.2f} eV")
```
## VASPFCP - job.py
```python
import os
from math import floor, ceil, sqrt, log
import numpy as np
from ase.io import read
from ase.calculators.vasp import Vasp
from ase.calculators.FCPelectrochem import FCP
from pathlib import Path

# Check if VASP path is set correctly, if not, exit early
vasp_path = os.environ.get('EBROOTVASP')
if not isinstance(vasp_path, str):
    exit()

# Manually set ASE's VASP command using the loaded module path
```
os.environ["VASP_COMMAND"] = f"mpirun {vasp_path}/bin/vasp_std"
os.environ["ASE_VASP_COMMAND"] = os.environ["VASP_COMMAND"]

```bash
# Get number of cores and calculate NPAR
num_cores = int(os.environ.get('SLURM_NTASKS', '32'))
```
ncore_setting = 4 if num_cores % 4 == 0 else 8

```bash
#Setting different potentials
```
NELECT0 = 401.0000
NELECT_guess =  400.7500

```bash
# Load the slab structure
cu_slab = read('yourstructureSOL-relax.traj')

# Set up the VASP calculator
```
calc = Vasp(
```
    algo='Fast',
    prec='Accurate',
    xc='PBE',
    encut=550,
    kpts=[3, 3, 1],
    ispin=2,
    ibrion=2,
    nsw=500,
    ismear=1,
    sigma=0.3,
    potim=0.5,
    isif=2,
    ediff=1e-5,
    ediffg=-0.02,
    isym=0,
    istart=0,
    ncore=ncore_setting,
    ivdw=12,
    lwave = True,
    lreal = 'Auto',
    lcharg = True,

    # VASPsol parameters:
    lsol=True, # Turns on implicit solvent
    eb_k=78.4, # Dielectric constant for water at room temp
    ldipol=False, # Dipole correction on
    idipol=3, # Dipole along z-axis (surface normal)
    lambda_d_k=3.0,
```
)

```bash
# Wrap with FCP constant-potential control
```
cal_FP = FCP(
```
    innercalc=calc, #The inner calculator here is the VASPSol calculation called 'calc' above
    U=-0.5,            # target potential (in volts vs SHE)
    NELECT0=NELECT0,  # neutral electron count
    NELECT=NELECT_guess,  # initial guess
    work_ref=4.6      # reference work function (SHE)
```
)

```bash
# Attach calculator
```
cu_slab.calc = cal_FP #Making sure the FCP calculator is the one used

```bash
# Run VASP (relaxation is internal)
```
final_energy = cu_slab.get_potential_energy()
print(f"Final relaxed energy: {final_energy:.2f} eV")

```bash
# Save final structure
from ase.io import write
```
write('yourstructure-FCP.traj', cu_slab)

```bash
# Save final energy to file
with Path("final.e").open("w", encoding="utf-8") as f:
    f.write(f"Final Energy: {final_energy:.2f} eV")
```

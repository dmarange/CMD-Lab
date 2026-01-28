from numpy import arange, linspace
from math import *
import os,sys
from numpy import linalg as LA
import time
from ase import Atoms
from ase import *
import numpy as np
from ase.data import reference_states as _refstate
from ase.parallel import paropen
from math import *
from ase.constraints import FixAtoms
from ase.optimize import QuasiNewton
from ase.io import *
from ase.io import read,write
from ase.lattice.cubic import SimpleCubicFactory
from ase.visualize import view
from ase import*
from ase import lattice
import numpy as np
from ase.lattice.compounds import L1_2
from ase.io.trajectory import PickleTrajectory
from ase.constraints import FixAtoms
from ase.optimize import QuasiNewton
from numpy import sqrt, pi
from numpy import arctan as atan
from ase import Atoms, Atom
from ase import io
from ase.constraints import FixAtoms
from ase.optimize import QuasiNewton
from ase.data import covalent_radii, atomic_numbers
from ase.optimize import BFGS
from ase.constraints import UnitCellFilter
from ase.units import Bohr, Hartree, Rydberg, fs
from ase.constraints import FixAtoms
import glob
import re
import subprocess
from string import Template
from ase.io import read
from ase.neighborlist import NeighborList
import numpy as np

number_of_nodes = 1#int(sys.argv[1])
number_cpu_node = 192#int(sys.argv[2])

IN = number_of_nodes * number_cpu_node

WORK_DIRS = []

#data_file_name = 'mb2.txt'
data_file_name = 'test.txt'
switch_key = 'w'
dirs = glob.glob('/scratch/aba229/metalBorides/runs_MB/MoB/001/COOH/2/')
#dirs = glob.glob('/scratch/aba229/metalBorides/runs_MB/CrB/001/NO2H/3/')
#dirs = glob.glob('/scratch/aba229/metalBorides/runs_MB2/*/*/*/*/')
#dirs = glob.glob('/scratch/aba229/metalBorides/runs_MB2/CrB2/*/*/*/')

print('\n >>>>>> Directory:', dirs , '\n >>>>>> Length of Directory:', len(dirs))
#re_run = False
re_run = True
cancel_jobs = True

# Get all job IDs for the current user
squeue_cmd = ["squeue", "-u", subprocess.getoutput("whoami"), "-h", "-o", "%i"]
job_ids = subprocess.getoutput(" ".join(squeue_cmd)).splitlines()

print("Job IDs:", job_ids, len(job_ids))

# Dictionary to map workdir -> job ID
workdir_to_job = {}

for job in job_ids:
    # Get the job info
    scontrol_cmd = ["scontrol", "show", "job", job]
    job_info = subprocess.getoutput(" ".join(scontrol_cmd))

    # Extract WorkDir
    workdir_line = [line for line in job_info.splitlines() if "WorkDir=" in line]
    if workdir_line:
        workdir = workdir_line[0].split("WorkDir=")[1].split()[0]
        WORK_DIRS.append(workdir)        
        workdir_to_job[workdir] = job

print("Workdir -> Job ID mapping:")
for wd, jid in workdir_to_job.items():
    print(f"{wd} -> {jid}")

def get_info(ase_slab):
#    slab = read(cif_file)
    Cell = ase_slab.get_cell()
    K = [0] * 3
    Density = 20
    for m in range(0,3):
        tkp = (float(Density/LA.norm(Cell[m])))
        kp = round(tkp+0.5)
        K[m] = kp
    nkpts = K[0]*K[1]*K[2]
    KP = tuple(K)
    def div(n):
        i = 1
        L = []
        while i <= n:
            if n % i == 0:
                L.append(i)
            i = i + 1
        return L
    DK = div(nkpts)
#    if 6nkpts % 2 == 0:
#    if Nall <= 300:
    tcpus = IN
    dcpu = div(tcpus)
    tcommon = list(set(DK).intersection(dcpu))
    common = sorted(tcommon, key=int,reverse=True)
    try:
        if len(common)>=1:
            pool = max(common)
    except:
        pool = 1
    return pool,K

def read_energies(self,getall=False):
    e0_values = []

    with open(self, 'r') as file:
        for line in file:
            match = re.search(r'E0= ([-+]?\d*\.\d+E[+-]?\d+)', line)
            if match:
                e0_values.append(float(match.group(1)))
    if e0_values:
        last_e0_value = e0_values[-1]
        return last_e0_value
    else:
        return None

def convergence(self):
    try:
        foutcar = open(self,"r")
        conv1 = False
        ionic_conv = False
        converged  = False
        linesoutcar = foutcar.readlines()
        if linesoutcar[-1][17:26] == 'Voluntary':
            conv1 = True
        for i in range(0,len(linesoutcar)):
            if linesoutcar[i][1:26] == 'reached required accuracy':
                ionic_conv = True
                break
        if conv1 == True and ionic_conv == True:
            converged = True
    except:
        converged  = False
    return converged


# Dissociation channels of interest
dissociation_channels = {
"NO2":      [["NO", "O"]],               # NO2 → NO + O
"NO2r":      [["NO", "O"],["N","O","O"]],               # NO2 → NO + O
"NO2CO2":   [["NO2", "CO2"]],            # NO2CO2 → NO2 + CO2
"NH2_CO2":  [["NH2_CO", "O"]],           # NH2_CO2 → NH2_CO + O
"NH2-COOH": [["NH2", "COOH"]],           # NH2-COOH → NH2 + COOH
"NH2_CO":   [["NH2", "CO"]],             # NH2_CO → NH2 + CO
"COOH":     [["CO2", "H"]],              # COOH → CO2 + H
}
molecule_atoms = {
    "NO2":     ["N", "O", "O"],
    "NO2r":     ["N", "O", "O"],
    "NO2H":     ["N", "O", "O", "H"],
    "CO2":     ["C", "O", "O"],
    "NO2CO2":  ["N", "O", "O", "C", "O", "O"],
    "NO":      ["N", "O"],
    "O":       ["O"],
    "NH2_CO2": ["N", "H", "H", "C", "O", "O"],
    "NH2-COOH":["N", "H", "H", "C", "O", "O", "H"],  # NH2 + COOH group
    "NH2_CO":  ["N", "H", "H", "C", "O"],
    "COOH":    ["C", "O", "O", "H"],
    "N":       ["N"],
    "CO":      ["C","O"]}


def identify_molecule(fragment_obj):
    # ----------------------
    # Identify_molecule function
    # INPUT: A list with atom object items
    # JOB: Goes through the list and extracts the .symbol from each item ----->
    # ------> if the list of symbols matches with our dictionary of identified molecules (molecule_atoms) ----> 
    # ------> returns the molecule name
    # ----------------------

    symbols = [frag.symbol for frag in fragment_obj]
    for mol_name, mol_atoms in molecule_atoms.items():
        if sorted(symbols) == sorted(mol_atoms):
            return mol_name
    return "Unknown"

def check_dissociation(atoms, adsorbate_identity_str):
    from ase.io import read
    from ase.neighborlist import NeighborList
    import numpy as np
    # IMPORTANT_NOTE ---> INPUT ---> #1 Trajectory object 
                                     #2 a string representing the adsorbate originally placed on slab
    
    #1 ----> obtains the index of elements that are N,O,C,H
    #2 ----> Builds molecular fragments based on bond constraints and atoms available
    #3 ----> If any of the molecular fragments match the original adsorbate identity which was given to the function, the dissociation is false.

    # ----------------------
    # Identify adsorbate indices in original slab
    # ----------------------
    adsorbate_symbols = ["N", "O", "C", "H"]
    adsorbate_indices_original = [i for i, atom in enumerate(atoms) if atom.symbol in adsorbate_symbols]

    # ----------------------
    # Repeat slab 3x3x1
    # ----------------------
    rep_x, rep_y, rep_z = 3, 3, 1
    atoms_repeated = atoms.repeat((rep_x, rep_y, rep_z))
    N_atoms_slab = len(atoms)

    # Map original adsorbate indices to repeated slab
    supercell_adsorbate_indices = []
    for ix in range(rep_x):
        for iy in range(rep_y):
            for iz in range(rep_z):
                shift = (ix + iy*rep_x + iz*rep_x*rep_y) * N_atoms_slab
                supercell_adsorbate_indices.extend([i + shift for i in adsorbate_indices_original])


    # ----------------------
    # Build Atoms object for all the repeated adsobrates
    # ----------------------
    adsorbate_atom_objects = Atoms([atoms_repeated[i] for i in supercell_adsorbate_indices])

    print('\n>>>>>>>>>This is adsorbate atoms objects\n', adsorbate_atom_objects)

    # ----------------------
    # Define maximum bond lengths for all relevant bonds
    # ----------------------
    max_bond_length = {
        ("C", "C"): 1.8,
        ("C", "N"): 1.7,
        ("C", "O"): 1.7,
        ("C", "H"): 1.2,
        ("N", "H"): 1.2,
        ("N", "O"): 1.5,
        ("O", "H"): 1.2,
    }

    # ----------------------
    # Build Fragments based on Depth First Search Algorithm (nodes are elements and connections are allowed bonds)
    # ----------------------
    ads_indices = range(len(adsorbate_atom_objects))
    fragments = []
    visited = set()

    for i in ads_indices:
        if i in visited:
            continue
        stack = [i]
        frag = []
        while stack:
            a = stack.pop()
            if a not in visited:
                visited.add(a)
                frag.append(a)
                for b in ads_indices:
                    if b != a:
                        bond = tuple(sorted([adsorbate_atom_objects[a].symbol,
                            adsorbate_atom_objects[b].symbol]))
                        if adsorbate_atom_objects.get_distance(a, b) < max_bond_length.get(bond, 2.0):
                            stack.append(b)
        fragments.append(frag)

    # ----------------------
    # Map fragment indices back to repeated slab
    # ----------------------
    fragments_atom_objects = [[adsorbate_atom_objects[i] for i in frag] for frag in fragments]
    
    # ----------------------
    # Create a list of identified fragments represented through symbols
    # ----------------------
    identified = [identify_molecule(frag) for frag in fragments_atom_objects]
    print('\n>>>>>>>>>> List of identified pieces\n', identified)
    
    #----------- Identity of Adsorbate-----------------
    true_identity = adsorbate_identity_str 
    if adsorbate_identity_str == 'NO2r':
        adsorbate_identity_str = 'NO2'
    if adsorbate_identity_str == 'NO2r_CO2':
        adsorbate_identity_str = 'NO2_CO2'
    if adsorbate_identity_str == 'HNO2':
        adsorbate_identity_str = 'NO2H'
    if adsorbate_identity_str == 'COOHr':
        adsorbate_identity_str = 'COOH'
    # Case [1] No fragment was found (i.e. clean)
    if len(identified) == 0: 
        return "Unknown", True
    
    # Case [2] If the original adsorbate string identifier (for example COOH) is in the list of fragments
    if adsorbate_identity_str in identified:
        return true_identity, False
        #return identified[identified.index(adsorbate_identity_str)], False

    # Case [3] If the name of the adsorbate string has '_' inside 
    if adsorbate_identity_str.find('_') != -1:
        pieces = adsorbate_identity_str.split('_')
        pieces = [i for i in pieces if i in molecule_atoms.keys()]
            
        # if the concatonated strings i.e. 'NO2_CO2' to 'NO2' + 'CO2' to 'NO2CO2'
        if pieces[0]+pieces[1] in identified:
            return true_identity, False
            #return identified[identified.index(pieces[0]+pieces[1])], False
        # if the adsorbate fragmented
        elif pieces[0] in identified and pieces[1] in identified:
            return pieces[0] + "——" + pieces[1], True
        else:
            return identified[0], True
    else:
        return "Unknown", True


g = open('slurm.template', 'r')
slurm_template = Template(g.read())
g.close()

k = open('adsorbate_restart.template', 'r')
adsorbate_template_restart = Template(k.read())
k.close()

#logfile_name = sys.argv[0]
direc = os.getcwd()+'/'
g = open(direc + data_file_name, switch_key)
root = "."


pwd = os.getcwd()


n_cancelled = 0

for i in range(len(dirs)):
    print(i)
    x = re.split("/", dirs[i])
    print("x:", x, len(x))
    base_dir = os.path.join("/", *x[:9])
    logdir = os.path.join(base_dir, "OUTCAR")
    oszcar = os.path.join(base_dir, "OSZICAR")
    contdir = os.path.join(base_dir, "CONTCAR") 
    efile = os.path.join(base_dir, "relaxed_pbe.e")
    workdir = base_dir
    configdir = base_dir    
    print('>>> Working Directory:',workdir,'\n >>> Energy File:',efile)
    alloy = str(x[5])
    facet = str(x[6])
    adsorbate = str(x[7])
    config = str(x[8])
    print('\n >>>>>>>>>>>>> x[5]:', alloy,
          '\n >>>>>>>>>>>>> x[6]:', facet, 
          '\n >>>>>>>>>>>>> x[7]:', adsorbate, 
          '\n >>>>>>>>>>>>> x[8]:', config)

    if workdir in WORK_DIRS:
        job_status = 'WAIT'
        job_id = workdir_to_job.get(workdir)       
    else:
        job_status = 'ENDED'
        job_id = 'NA'        

    # base_dir is your directory path
    try:
        cif_files = glob.glob(os.path.join(base_dir, "*.cif"))

        if cif_files:
            in_traj_dir = cif_files[0]  # take the first CIF file found
    except:
        in_traj_dir = os.path.join(base_dir, "slab.traj")
    in_traj = read(in_traj_dir)
    
    if os.path.exists(logdir) and os.path.exists(contdir):
        try:
             last_atoms = read(logdir)
        except:
            try:
                last_atoms = read(contdir)
            except:
                print('----------No trajectory could be read---------------')
        if convergence(logdir) and adsorbate != 'CLEAN':
            E = float(read_energies(oszcar))
            in_traj = read(in_traj_dir)
            status, dissociated = check_dissociation(last_atoms, adsorbate)

            print("4th adsorbate status:", status)
            print("Is dissociated?", dissociated)

            g.write("%s/%s/%s/%s/%s/%s/%s/%s/%s/" % (alloy, facet, adsorbate, config, str(E), dissociated, job_status, job_id, status))
            g.write("\n")#        
            if job_status == 'WAIT' and cancel_jobs:
                subprocess.run(["scancel", job_id])           
                n_cancelled+=1
                print('Cancelled due to convergance')
        print('--------------------------------------------------------')
        if not convergence(logdir) and adsorbate != 'CLEAN':
            try: 
                in_traj = read(in_traj_dir)
                status, dissociated = check_dissociation(last_atoms, adsorbate)

                print("4th adsorbate status:", status)
                print("Is dissociated?", dissociated)

                E = 'Not converged'
                g.write("%s/%s/%s/%s/%s/%s/%s/%s/%s/" % (alloy, facet, adsorbate, config, E, dissociated, job_status, job_id, status))                
                g.write("\n")#

                if job_status == 'WAIT' and dissociated and cancel_jobs:
                    subprocess.run(["scancel", job_id])
                    print('job cancelled due to diss')
                    n_cancelled+=1                    
                if job_status != 'WAIT' and not dissociated and re_run:
                    try:
                        kpts=get_info(in_traj)[1]                    
                        slabdir= os.path.join(base_dir, "slab.traj")                        
                        atoms = read(slabdir)
                        # Check constraints
                        constraints = atoms.constraints

                        # If FixAtoms exists, extract indices
                        fixed_indices = []
                        for c in constraints:
                            if isinstance(c, FixAtoms):
                                fixed_indices.extend(c.index)

                        filename = 'run.py'
                        namejob = '%s-%s-%s-%s' % (alloy,facet,adsorbate, config)
                        jobname = "bash.slurm"
                        h = open(os.path.join(configdir, jobname), 'w')
                        h.write(slurm_template.safe_substitute({'number_of_nodes':number_of_nodes,'number_cpu_node':number_cpu_node,'namejob':namejob}))
                        h.close()

                        f = open(os.path.join(configdir, filename), 'w')

                        f.write(adsorbate_template_restart.safe_substitute({'alloy':alloy,'kpts':kpts,'fixed_indices':fixed_indices}))
                        f.close()
                        zip_path = f"{workdir}/run0_zipped.tar.gz"

                        if os.path.exists(zip_path):
                            print(f"{zip_path} already exists! Rename it or delete it before creating a new archive.")
                        else:
                            os.system(f"tar -czvf {zip_path} -C {workdir} .")
    
                        # Step 1: Backup VASP files inside workdir
                        os.system(f"cd {workdir} && cp CONTCAR CONTCAR.old && cp WAVECAR WAVECAR.old && cp CHGCAR CHGCAR.old")

                        os.chdir(workdir)                        
                        PWD = os.getcwd() 
                        print("PWD:",PWD)
                        os.system("sbatch  "+jobname)
                        os.chdir(pwd)
                        print('--------------------------------------------------------')
                    except:
                        print('error occured for re-running')
            except Exception as e:
                print(f"Error processing {logdir}: {e}")
                g.write("%s/%s/%s/%s/%s/%s/%s/%s/%s/" % (alloy, facet, adsorbate, config, 'traj error', 'Unknown', job_status, job_id, 'Unknown'))
                g.write("\n")
                print('--------------------------------------------------------')

    if os.path.exists(logdir) and adsorbate == 'CLEAN':
        #breakpoint()
        if convergence(logdir):
            E = float(read_energies(oszcar))
            if job_status == 'WAIT' and cancel_jobs:
                subprocess.run(["scancel", job_id])
                n_cancelled+=1
        if not convergence(logdir):            
            E = 'not converged'    
        g.write("%s/%s/%s/%s/%s/%s/%s/%s/" % (alloy, facet, adsorbate, config, str(E), False, job_status, job_id))            
        g.write("\n")
        print('--------------------------------------------------------')

    if not os.path.exists(logdir):
        E = 'No OUTCAR'
        g.write("%s/%s/%s/%s/%s/%s/%s/%s/" % (alloy, facet, adsorbate, config, E, False, job_status, job_id))
        g.write("\n")
        if job_id == "NA" and re_run:
            current_directory = os.getcwd()
            os.chdir(workdir)
            os.system("sbatch  "+"job.slurm")
            os.chdir(current_directory)
        print('--------------------------------------------------------')

f = open(data_file_name, 'r')
lines = f.read().splitlines()
f.close()
print("n_cancelled:",n_cancelled)

# ~/.bashrc --My defualt merged Quantum ESPRESSO + VASP environment for FIR (Alliance Canada)

# ------------------------------------------------------------
# 1) Source global definitions (system‑wide bashrc)
# ------------------------------------------------------------
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# ------------------------------------------------------------
# 2) Shell history — keep plenty of commands
# ------------------------------------------------------------
export HISTSIZE=10000          # in‑session history lines
export HISTFILESIZE=100000     # lines saved to ~/.bash_history

# ------------------------------------------------------------
# 3) Aliases
# ------------------------------------------------------------
# Generic
alias ll='ls -al'
alias la='ls -a'
alias ag='ase gui'

# Quick Cedar SSH shortcut
alias cedar='ssh -X your_username@any_cluster.alliancecan.ca'

# View all of your jobs in the queue (incl. completed/failed)
alias sq='squeue -u ${USER} --state=ALL --format="%.9i %.3t %.10L %.5u %.15a %.15j %.4C %.25N %.80Z"'

# Remove the usual VASP output files from the current directory and below
alias remove_vasp_files='find . -type f \( -name "CONTCAR" -o -name "CHGCAR" -o -name "ase-sort.dat" -o -name "XDATCAR" -o -name "POSCAR" -o -name "IBZKPT" -o -name "KPOINTS" -o -name "PCDAT" -o -name "CHG" -o -name "DOSCAR" -o -name "INCAR" -o -name "OSZICAR" -o -name "REPORT" -o -name "WAVECAR" -o -name "EIGENVAL" -o -name "OUTCAR" -o -name "POTCAR" -o -name "vasp.out" -o -name "vaspout.h5" -o -name "vasprun.xml" \) -exec rm {} +'

# ------------------------------------------------------------
# 4) VASP environment (used by ASE + VASP modules)
# ------------------------------------------------------------
# NOTE: EBROOTVASP is set automatically when you `module load vasp`.
export VASP_COMMAND="mpirun ${EBROOTVASP}/bin/vasp_std"
export VASP_HOME="$HOME/vasp"
export VASP_PP_PATH="$VASP_HOME/vasp_PP"
export VASP_VDW="$VASP_HOME/vasp-support"
export ASE_VASP_COMMAND="$VASP_COMMAND"

# ------------------------------------------------------------
# 5) SLURM default account (so you don’t have to specify every time)
# ------------------------------------------------------------
export SLURM_ACCOUNT="rrg-karamad"
export SBATCH_ACCOUNT="$SLURM_ACCOUNT"
export SALLOC_ACCOUNT="$SLURM_ACCOUNT"

# ------------------------------------------------------------
# 5) Python + ASE environment (virtualenv-based)
# ------------------------------------------------------------

# Path to your virtual environment
export VENV_PATH="/home/your_path/virtenv"
export ASE_ENV="/home/your_path/virtenv/bin/activate"
export VIRTUAL_ENV=$VENV_PATH

# Add virtualenv Python packages to Python path
export PYTHONPATH="$VENV_PATH/lib/python3.11/site-packages:$PYTHONPATH"

# Always use the venv's Python
export PATH="$VENV_PATH/bin:$PATH"

# Optional alias for manual activation
alias env='source $VENV_PATH/bin/activate'
alias deac='deactivate'
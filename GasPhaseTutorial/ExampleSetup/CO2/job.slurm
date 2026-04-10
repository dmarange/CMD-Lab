#!/bin/bash
#SBATCH --job-name=CO2_DFT_ZPETS
#SBATCH --time=05:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=32
#SBATCH --mem-per-cpu=3900
#SBATCH --account=rrg-karamad

# Start timing the entire job
start_time=$(date +%s)

# Load necessary modules
module purge
module load StdEnv/2023 intel/2023 intelmpi/2021.9.0
module load python/3.11.5 scipy-stack
module load vasp/6.4.2

# Check if essential modules loaded correctly
if [[ $(module list 2>&1 | grep 'intel/2023') == "" || \
      $(module list 2>&1 | grep 'python/3.11.5') == "" || \
      $(module list 2>&1 | grep 'vasp/6.4.2') == "" ]]; then
    module list
    echo "Your modules are not loaded correctly for VASP. Cancelling job... "
    exit 1
else
    module list
    echo "Modules loaded correctly. Activating Python virtual environment..."
fi

# Activate your bashrc (to pick up aliases or other config if needed)
if test -e "$HOME/.bashrc"; then
    source "$HOME/.bashrc"
fi

# Activate your virtualenv
source /home/your_path/virtenv/bin/activate

# Set ASE VASP command
export ASE_VASP_COMMAND="srun ${EBROOTVASP}/bin/vasp_std"

# Echo key environment variables
echo "EBROOTVASP=$EBROOTVASP"
echo "VASP_HOME=$VASP_HOME"
echo "VASP_PP_PATH=$VASP_PP_PATH"
echo "ASE_VASP_COMMAND=$ASE_VASP_COMMAND"
ls -ld $VASP_PP_PATH

echo "####################################"
echo "# We are now running job ${SLURM_JOB_ID}! #"
echo "####################################"

# Get the current working directory
cwd=$(pwd -P)

# Start the Python script using your virtualenv Python
time python run.py

# End timing
end_time=$(date +%s)
elapsed_time=$((end_time - start_time))
elapsed_time_hms=$(printf "%02d:%02d:%02d" $((elapsed_time / 3600)) $(( (elapsed_time % 3600) / 60 )) $((elapsed_time % 60)))
echo "Task ${SLURM_JOB_ID} completed in $elapsed_time_hms (HH:MM:SS)."

## CO2 Example
This folder contains an example CO2 gas-phase workflow.
Copy these example files (in CO2 directory) into an exmaple folder in your FIR cluster:

- `make_CO2_traj.py`
- `run.py`
- `job.slurm`

## Step 1. Make `co2.traj`

Run:

```bash
python make_CO2_traj.py
```

This writes:

```bash
co2.traj
```

`run.py` uses this file as the gas-phase CO2 structure input.

## Step 2. Check `run.py`

Make sure this line points to the same trajectory file:

```python
atoms = read("co2.traj")
```

Also update any molecule-specific thermochemistry settings in `run.py` if needed.

## Step 3. Submit the Job

Run:

```bash
sbatch job.slurm
```

This submits `run.py` through the SLURM job file.

## Step 4. Monitor the Job

Check queue status with:

```bash
sq
```

## Expected Output

After the job completes, you should see files such as:

- `co2.traj`
- `dft.energy`
- `relaxed.traj`
- `CONTCAR`
- `OUTCAR`
- `final.energy`

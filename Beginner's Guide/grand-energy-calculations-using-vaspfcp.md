# Grand Energy Calculations Using VASPFCP

https://github.com/hellozhaoming/FCP-vasp-ase
VASPFCP Workflow
1. Regular VASP
Regular VASP run to get the number of electrons NELECT0 in the OUTCAR file and a relaxed trajectory to be used later in VASPSol runs.

In OUTCAR after run completes:
```
NELECT =     401.0000    total number of electrons
```
2. VASPSol
VASPSol runs for each potential shift in the range -0.5V to 0.5V. In the VASPSol parameters, ldipol (Dipole correction) is set to False due to runs crashing when set to True.

These VASPSol runs give the relaxed solvated trajectories that will be used in VASPFCP runs.

3. VASPFCP
The final VASPFCP run will give the grand energy from the relaxed VASPSol trajectory. The only change is wrapping the VASPSol calculator in the VASPFCP inner calculator. The NELECT_guess value here is nelect_value from the script above, assuming the VASPSol run converged.

4. Results
Once the job is complete, log-fcp.txt and tmp-log-FCP.txt files will be created. The log-fcp.txt file has the final grand energies.

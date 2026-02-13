# DFT Energy Calculations Using Quantum ESPRESSO

Quantum ESPRESSO is used to run your simulations on Compute Canada clusters. To perform a calculation, you will need to prepare several input and job-related files

- Transfer the script_maker folder to your Compute Canada using:

```bash
scp -r path_to_your_script_maker_folder username@cluster.computecanada.ca:compute_canada_directory_path

i.e scp -r ./script_maker/ username@cedar.computecanada.ca:/home/username/scratch
```
- Create a job file where you will transfer your:
- script_maker.py (link)
- job.sh (link)
- A trajectory file

The compute_canada_directory_path must be set in your script_maker.py

- Make sure all relevant details in the scripts are updated with your information. Then, run script_maker.py to generate your input file (e.g., input.in), and submit your job using sbatch job.sh.

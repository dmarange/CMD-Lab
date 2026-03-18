# Bash Profile Setup - Optional

One of the easiest ways to improve your workflow when working with ASE and Compute Canada clusters is by setting up aliases in your terminal. Aliases let you create shortcuts for long commands, reducing repetitive typing and making your work more efficient.

To set these up, you’ll need to edit your shell configuration file—commonly .bashrc or .bash_profile (depending on your system and terminal). For Git Bash, you can modify the .bash_profile file using the following commands:

-Open for editing:
```bash
vi ~/.bash_profile
```
OR
```bash
vi ~/.bashrc
```
-Save changes:
```bash
source ~/.bash_profile
```
OR
```bash
source ~/.bashrc
```

Inside the editor, press **I** to enter insert mode and add your custom aliases. Once finished, press **ESC** and type **:wq** (write and quit).

Here are some useful examples:

-Login in to compute canada cluster:
```
alias PUTANYTHINGHERE= “ssh -X USERNAME@CLUSTER.computecanada.ca”
```
Example:
```
alias fir="ssh -X jdoe@fir.computecanada.ca"
alias graham="ssh -X jdoe@graham.computecanada.ca"
alias nibi="ssh -X jdoe@nibi.computecanada.ca"
```
-Using ag instead of typing ase gui to view trajectory files:
```
alias ag="ase gui"
```
## NEXT 
[Setting Up Python On Alliance Canada Cluster](./setting-up-python-on-compute-canada-cluster.md)

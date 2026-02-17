# GET FILE
This python script is the result scraper! It will go through all the final trajectories in a specified directory and analyze whether or not the 
molecular species placed on the surface has *dissociated* into smaller pieces. It will also collect information if the job has converged or not. Once it is done iterating 
through all the directory pathways that you have specified, it outputs all the result in a text file.

## How to use
There are mainly 5 variables that needs to be changed based on your use case.
1. [`dirs`](get.py#L54) this variable is the pathway to your job directories.
2. [`data_file_name`](get.py#L52) name of the output results file.
3. [`switch_key`](get.py#L53) between 'a' and 'w' which will either append the results to the text file (if it exists) or it will overwrite it. 
4. [`re_run`](get.py#L61) this is a boolean key when set to `True` will resubmit *unfinished* jobs. (an *unfinished job* is a calculation that has not converged AND the adsorbate is still intact)
5. [`cancel_jobs`](get.py#L62) this is another boolean key when set to `True` will cancel an active job if it has either converged OR the adsorbate has dissociated. 

variables 4 and 5 are ***super important***.

## Logic

### How does it recognize if a molecule has *dissociated*?

This is done by chemical formula. The script will `read` the `CONTCAR` (if it can't then `OUTCAR`) and builds an index list of every atom object that is either `N, O, C, H` to 
seperate the atoms of the adsorbate from the surface. 

The list of indicies will be used to build fragments by doing a [depth-first-search algorithm](get.py#L257-273). Essentially it will take an atom object 
and check its distance with every other atom in the list, if it is within limits of a sensible chemical bond, then it will connect them into fragment. This process is repeated until all the
atoms in this list are made into fragments. 

Each fragment is then symbolized and checked against a pre-defined dictionary of symbols that match a chemical formula.

If the chemical formula that it finds matches the name of the adsorbate in the trajectory pathway. Then it is not dissociated. 

Here is an example:

List of indicies: `[1,22,34,56,79,118]`

List of Fragments: `[[1,34],[22,56,79,118]]`

Symbolized: `[['N','O'],['N','O','O','H']]`

Checked if it exists in the dictionary ==> `[['NO'],['HNO2']]`

Pathway to job: `.../Cr/001/HNO2/1` ==> adsorbate is found in the list. 

It is not dissociated!!

### Important caveats and disclamers!

1) If the surface has any `N, O, C, H` then it will also be included in the list of indicies, this may or may not alter the results.
2) You set the sensible bond distances! in the [`check_dissociation`](get.py#L197) function there is a dictionary called [`max_bond_length`](get.py#L240) which mainly determines if two elements can be considered covalently bound or not.
3) The fragment identifier function [`identify_molecule`](get.py#L182) can only return a chemical formula if the dictionary [`molecule_atoms`](get.py#L166) assigns
    the sequence of elements to a chemical formula. (e.g. a fragment was extracted as `['N','O','H','H']` but the `molecule_atoms` doesn't have an entry of `"NOH2": ["N", "O", "H", "H"]` then the output will be `unknown`)
 

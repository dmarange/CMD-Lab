# DFT Energy Calculations Using Vienna Ab initio Simulation Package (VASP)

VASP is used to run your simulations on Compute Canada clusters. To perform a calculation, you will need to prepare several input and job-related files. Some workarounds need to run VASP 6, which will be mentioned below, depending on the errors you get.

Error 1 - Key Error
If you get an error that looks like this:

```
KeyError: 'Cu/0e71e558f37'
```
Or,
```
KeyError: 'Sc_sv'
```
This is due to VASP reading the pseudopotentials with strings attached to the element name you are looking for. The fix requires a modification to symbols.py in the ase directory you are using to access ase modules. My location is YourVirtenvPath/lib/python3.11/site-packages/ase/symbols.py. This Fix still uses the correct pseudopotentials for Sc_sv which means:
_sv = semi-valence -> additional s and p states from the semicore are included in the valence.

_pv = p-valence -> the p semicore states are explicitly treated as valence electrons.

No suffix = "standard" -> only the minimal valence states are treated as valence; semicore states remain frozen in the core.

Unmodified symbols.py version (symbols2numbers)
```python
def symbols2numbers(symbols) -> List[int]:
    if isinstance(symbols, str):
        symbols = string2symbols(symbols)
    numbers = []
    for s in symbols:
        if isinstance(s, str):
            s = s.strip().split('/')[0] # Get rid of slash and anything after
            numbers.append(atomic_numbers[s])
        else:
            numbers.append(int(s))
    return numbers
```
Modified symbols.py version (symbols2numbers)
```python
def symbols2numbers(symbols) -> list[int]:
    if isinstance(symbols, str):
        from ase.symbols import string2symbols
        symbols = string2symbols(symbols)
    numbers = []
    for s in symbols:
        if isinstance(s, str):
            # Drop slash suffix (e.g. Cu/0e71e558f37 -> Cu)
            s = s.strip().split('/')[0]
            # Drop underscore pseudopotential tags (e.g. Zr_sv -> Zr)
            if "_" in s:
                s = s.split("_")[0]
            numbers.append(atomic_numbers[s])
        else:
            numbers.append(int(s))
    return numbers
```
Error 2 - OUTCAR Magnetic moment data

The error in your OUTCAR will say:

```
UserWarning: Magnetic moment data not written in OUTCAR (LORBIT<10), setting magnetic_moments to zero. Set LORBIT>=10 to get information on magnetic moments warn('Magnetic moment data not written in OUTCAR (LORBIT<10),'
```
You ran VASP with the default LORBIT setting (LORBIT = -1, i.e. no projection data written).

- You can ignore this warning if you don't care about site-resolved magnetism.

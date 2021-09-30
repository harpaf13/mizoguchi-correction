# miz_correction.py


Calculates the Mizoguchi et al. correction to the transition energy \
for plane wave pseudopotential calculated EELS/XAS spectra from a .castep file.\
Requires castep to be on your path, and the .castep, .cell, and .param files to be\
in the current working directory. This calculation will perform a castep dryrun.
Example usage is `./miz_correction.py -e S -i LiFeS-1Li-supercell-S1-xas -t -94950.57862045 -exe castep19`\
Which would have output 2479.154058 eV

# SAMPLE OUTPUT
 Example usage is `./miz_correction.py -e Al -i Al2O3 -t -138442.0450689 -exe castep19`\
 Getting Ecore for Al in Al2O3.castep
 RUNNING CASTEP DRYRUN CALC...
 The E_core(atom) for Al in Al2O3 is 2097.432200
 Now calculating full Mizoguchi correction with supplied ground state energy of -138442.045069 eV
 Mizoguchi corrected transition energy is 1575.658422
 Finished.

# To Do

- Make this work with multiple castep files 
- Can you generalize so you don't need to put in --element X
- Write out .castep files for singlepoint calc?
- Could also add in plotting functionality (not sure this is the order we want to do things in)
- Need to modify OptaDOS still to allow a new variable to to shift the results by

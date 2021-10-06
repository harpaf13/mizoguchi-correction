#!/usr/bin/python
import os,sys
import argparse
import datetime


    
def get_Ecore(element,infile,exe,outfile):
    """Calculate the energy difference between the excited and valence states for the pseudopotentials
    used in the coreloss calculation"""
    
    outfile.write('''
+-------------------------------- ECORE -------------------------------------+
''')

    # First open the castep file in <infile>.castep
    try:
        castepfile = open('%s.castep'%infile).readlines()
    except:
        outfile.write(('\n%s.castep not found in folder'%infile))
        outfile.write(('...EXITING...'))
        exit()
    

    E_exc_all = 0
    E_gs_all = 0
    E_exc_val = 0
    E_gs_val = 0
    # Read through the castep file to get each variable needed for Ecore
    for i,line in enumerate(castepfile):
        if ('Atomic calculation' in line) and ('%s:'%element in line):
            E_exc_all = float(castepfile[i+2].split(' ')[-2])
        if ('Pseudo atomic' in line) and ('%s:'%element in line):
            E_exc_val = float(castepfile[i+2].split(' ')[-2])
        if ('Pseudo atomic' in line) and ('%s '%element in line):
            E_gs_val = float(castepfile[i+2].split(' ')[-2])

        #this linesearching cannot distinguish between multiple castep runs in one file and will just find the last energy supplied
        if 'DRYRUN' in line: 
            outfile.write('\nWARNING you have already run a DRYRUN calculation within this %s.castep file'%infile)
            outfile.write('Final correction may not be accurate, remove this dryrun calculation from the %s.castep file'%infile)
            outfile.write('...EXITING...')
            exit()

    outfile.write('''|  E excited all electrons                   : {:<10.2f} eV                 |
'''.format(E_exc_all))
    outfile.write('''|  E excited valence electrons               : {:<10.2f} eV                 |
'''.format(E_exc_val))
    outfile.write('''|  E ground state valence electrons          : {:<10.2f} eV                 |
'''.format(E_gs_val))
    
    # Check to be sure all values are supplied
    if E_exc_all == 0 or E_exc_val == 0 or E_gs_val == 0:
        outfile.write('One or more values above is 0 eV')
        outfile.write('Failed to find all values for Ecore in %s.castep'%infile)
        outfile.write('...EXITING...')
        exit()

   
    # Get E_gs_all by doing dryrun
    try:
        cellfile = open('%s.cell'%infile).readlines()
        newcellfile = open('%s-dryrun.cell'%infile,'w')
        for line in cellfile:
            if '%s:'%element in line and '{' in line:
                newline = line.split('{')[0]
                newcellfile.write('%s\n'%newline)
            else:
                newcellfile.write(line)
        newcellfile.close()
        os.system('cp %s.param %s-dryrun.param'%(infile,infile))
        if os.path.isfile('%s-dryrun.castep'%infile):
            print('CASTEP DRYRUN ALREADY COMPLETED...')
        else:
            print('RUNNING CASTEP DRYRUN CALC...')
            os.system('%s --dryrun %s-dryrun'%(exe,infile))
    except:
        outfile.write('CASTEP --dryrun execution failed...check your castep binary is on your path')
        outfile.write('...EXITING...')
        exit()
        
    newcastepfile = open('%s-dryrun.castep'%infile).readlines()
    # If the dryrun is successful, get the E_gs_all
    for i,line in enumerate(newcastepfile):
        if ('Atomic calculation' in line) and ('%s:'%element in line):
            E_gs_all = float(newcastepfile[i+2].split(' ')[-2])

    outfile.write('''|  E ground state all electrons              : {:<10.2f} eV                 |
'''.format(E_gs_all))

    if E_gs_all == 0:
        outfile.write('\nFailed to find E ground state all electrons in %s-dryrun.castep'%infile)
        outfile.write('...EXITING...')
        exit()

    Ecore = (E_exc_all - E_gs_all) - (E_exc_val - E_gs_val)
    outfile.write('''+----------------------------------------------------------------------------+
''')
    outfile.write('''|  E core from pseudopotentials              : {:<10.2f} eV                 |
'''.format(Ecore))
    outfile.write('''+----------------------------------------------------------------------------+
''')
    return Ecore

def get_exc_cell(element,infile):
    '''Find the excited state total energy calculated as part of the core loss calculation
    '''

    outfile.write('''
+-------------------------- MIZOGUCHI CORRECTION ----------------------------+
''')

    # First open the castep file in <infile>.castep
    try:
        castepfile = open('%s.castep'%infile).readlines()
    except:
        outfile.write('%s.castep not found in folder'%infile)
        outfile.write('...EXITING...')
        exit()

    E_exc_cell = 0
    for i,line in enumerate(castepfile):
        if 'NB est. 0K energy' in line:
            E_exc_cell = float(line.split('=  ')[1].split(' ')[0])
        
    if E_exc_cell == 0:
        outfile.write('Final energy in %s.castep not found'%infile) 
        outfile.write('...EXITING...')
        exit()

    outfile.write('''|  Core hole total energy                    : {:<10.2f} eV                 |
'''.format(E_exc_cell))

    return E_exc_cell


def write_header(outfile,e):
     
    outfile.write('Mizoguchi Correction: Execution started on %s/%s/%s at %s:%s:%s\n'%(e.day,e.month,e.year,e.hour,e.minute,e.second))
    
    outfile.write('''+============================================================================+
|                                                                            |
|            M M  IIIII  ZZZZZ  OOO   GGG  U   U  CCC  H  H IIIII            |
|           M M M   I       Z  O   O G     U   U C   C H  H   I              |
|           M   M   I      Z   O   O G  GG U   U C     HHHH   I              |
|           M   M   I     Z    O   O G   G U   U C   C H  H   I              |
|           M   M IIIII  ZZZZZ  OOO   GGG   UUU   CCC  H  H IIIII            |
|                                                                            |
+----------------------------------------------------------------------------+
''')
    return

def flags(args,outfile):
    outfile.write('''
+-------------------------------- FLAGS -------------------------------------+
''')

    outfile.write('''|  Element with core hole                    : {:30}|
'''.format(args.element))
    
    outfile.write('''|  Input file to read from                   : {:30}|
'''.format(args.inputfile))

    if args.totalenergy:
        outfile.write('''|  Non core hole ground state energy         : {:<10.2f} eV                 |
'''.format(args.totalenergy))
    else:
        outfile.write('''|  Non core hole ground state energy         :  None                         |
'''%args.totalenergy)

    outfile.write('''|  CASTEP Executable                         : {:30}|
'''.format(args.executable))
    outfile.write('''+----------------------------------------------------------------------------+
''')


def write_odi_file(infile,E_TE):
    odifile = open('%s.odi'%infile,'a+')
    write_mizo = True
    for line in odifile:
        if 'mizoguchi_correction' in line:
            write_mizo = False
    if write_mizo: 
        odifile.write('mizoguchi_correction : %f'%E_TE)
    odifile.close()
    return
#############
#Main script#
#############
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''Calculates the Mizoguchi et al. correction to the transition energy \
            for plane wave pseudopotential calculated EELS/XAS spectra from a .castep file.\
            Requires castep to be on your path, and the .castep, .cell, and .param files to be\
            in the current working directory. This calculation will perform a castep dryrun.
            Example usage is `./miz_correction.py -e S -i LiFeS-1Li-supercell-S1-xas -t -94950.57862045 -exe castep19`\
            Which would have output 2479.154058 eV
            ''')


    #Options
    parser.add_argument('-e','--element',type=str,required=True,
                        help='Element on which the core loss calculation has been performed. This is the elment that should have the core hole placed on it')

    parser.add_argument('-i', '--inputfile', type=str,required=True,
                        help='Name of the input file (<input>.castep only) in which the core loss calculation has been performed')
    parser.add_argument('-t', '--totalenergy', type=float,
                        help='Total energy of unit cell without a core hole. If included this will calculate the full Mizoguchi corrected transition energy using this value as the total singlepoint free energy (E-0.5TS)')
    parser.add_argument('-exe', '--executable', type=str,required=True,
                        help='This is the castep binary name e.g. castep.mpi or castep19.1 which should be on your $PATH')

    starttime = datetime.datetime.now()
    args = parser.parse_args()

    # remove the .castep ending in order to use this variable later
    if args.inputfile.endswith('.castep'):
        args.inputfile = args.inputfile.split('.castep')[0]

    outfile = open('%s-mizoguchi.out'%args.inputfile,'w')


    # Create the output file for the Mizoguchi correction
    write_header(outfile,starttime)

    # Write out which options we are using
    flags(args,outfile)

    # Get the second term of E_TE the core orbitals difference in energy between excited and ground state
    Ecore = get_Ecore(element=args.element,infile=args.inputfile,exe=args.executable,outfile=outfile)

    if args.totalenergy:
        E_gs_cell = args.totalenergy
        E_exc_cell = get_exc_cell(element=args.element,infile=args.inputfile)
        E_TE = (E_exc_cell - E_gs_cell)+Ecore
        outfile.write('''+----------------------------------------------------------------------------+''')
        outfile.write('''
|  Mizoguchi correction to E_TE              : {:<10.2f} eV                 |'''.format(E_TE))
        outfile.write('''
+----------------------------------------------------------------------------+''')

    else:
        outfile.write('No ground state energy supplied, exiting without calculating full Mizoguchi correction.')
        outfile.write('...EXITING...')
        exit()
    

    write_odi_file(args.inputfile,E_TE)
    outfile.write('''                                                                              ''')
    outfile.write('''
+----------------------------------------------------------------------------+''')
    outfile.write('''
|                                  FINISHED                                  |''')
    outfile.write('''
+----------------------------------------------------------------------------+''')


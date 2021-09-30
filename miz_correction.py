#!/usr/bin/python
import os,sys
import argparse
import datetime


    
def get_Ecore(element,infile,exe):
    """Calculate the energy difference between the excited and valence states for the pseudopotentials
    used in the coreloss calculation"""
    
    # First open the castep file in <infile>.castep
    try:
        castepfile = open('%s.castep'%infile).readlines()
    except:
        print('%s.castep not found in folder'%infile)
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
            print('WARNING you have already run a DRYRUN calculation within this %s.castep file'%infile)
            print('Final correction may not be accurate, remove this dryrun calculation from the %s.castep file'%infile)
            print('Exiting...')
            exit()
    
    # Check to be sure all values are supplied
    if E_exc_all == 0 or E_exc_val == 0 or E_gs_val == 0:
        print(E_exc_all)
        print(E_exc_val)
        print(E_gs_val)
        print('Failed to find all values for Ecore in %s.castep'%infile)
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
        print('CASTEP --dryrun execution failed...check your castep binary is on your path')
        exit()
        
    newcastepfile = open('%s-dryrun.castep'%infile).readlines()
    # If the dryrun is successful, get the E_gs_all
    for i,line in enumerate(newcastepfile):
        if ('Atomic calculation' in line) and ('%s:'%element in line):
            E_gs_all = float(newcastepfile[i+2].split(' ')[-2])

    if E_gs_all == 0:
        print(E_gs_all)
        print('Failed to find E_gs_all in %s-dryrun.castep'%infile)
        exit()

    Ecore = (E_exc_all - E_gs_all) - (E_exc_val - E_gs_val)
    return Ecore

def get_exc_cell(element,infile):
    '''Find the excited state total energy calculated as part of the core loss calculation
    '''

    # First open the castep file in <infile>.castep
    try:
        castepfile = open('%s.castep'%infile).readlines()
    except:
        print('%s.castep not found in folder'%infile)
        exit()

    E_exc_cell = 0
    for i,line in enumerate(castepfile):
        if 'NB est. 0K energy' in line:
            E_exc_cell = float(line.split('=  ')[1].split(' ')[0])
        
    if E_exc_cell == 0:
        print('Final energy in %s.castep not found'%infile) 
        exit()


    return E_exc_cell


def write_header(outfile,e):
     
    outfile.write('Mizoguchi Correction: Execution started on %s/%s/%s at %s:%s:%s\n'%(e.day,e.month,e.year,e.hour,e.minute,e.second))
    
    outfile.write('''+===========================================================================+\n
 |                                                                           |
 |            M M  IIIII  ZZZZZ  OOO   GGG  U   U  CCC  H  H IIIII           |
 |           M M M   I       Z  O   O G     U   U C   C H  H   I             |
 |           M   M   I      Z   O   O G  GG U   U C     HHHH   I             |
 |           M   M   I     Z    O   O G   G U   U C   C H  H   I             |
 |           M   M IIIII  ZZZZZ  OOO   GGG   UUU   CCC  H  H IIIII           |
 |                                                                           |
 +---------------------------------------------------------------------------+
''')
    return

def flags(args,outfile):
    outfile.write('''
 +-------------------------------- FLAGS -------------------------------------+
''')

    outfile.write('''
 |  Element with core hole                    :  %.2s                         |
'''%args.element)
    
    outfile.write('''
 |  Input file to read from                   :  %.20s     |
'''%args.inputfile)

    if args.totalenergy:
        outfile.write('''
 |  Non core hole ground state energy         :  %.2f                       |
'''%args.totalenergy)
    else:
        outfile.write('''
 |  Non core hole ground state energy         :  None                         |
'''%args.totalenergy)

    outfile.write('''
 |  CASTEP Binary                             :  %s  |
'''%args.executable)
    outfile.write('''
 +----------------------------------------------------------------------------+
''')


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
    print('\nGetting Ecore for %s in %s.castep'%(args.element,args.inputfile))
    Ecore = get_Ecore(element=args.element,infile=args.inputfile,exe=args.executable)

    print(r'The E_core(atom) for %s in %s is %f'%(args.element,args.inputfile,Ecore))

    if args.totalenergy:
        print('Now calculating full Mizoguchi correction with supplied ground state energy of %f eV'%args.totalenergy) 
        E_gs_cell = args.totalenergy
        E_exc_cell = get_exc_cell(element=args.element,infile=args.inputfile)
        E_TE = (E_exc_cell - E_gs_cell)+Ecore
        print('Mizoguchi corrected transition energy is %f eV'%E_TE)

    else:
        print('No ground state energy supplied, exiting without calculating full Mizoguchi correction.')
        exit()
    
    print('Finished.')

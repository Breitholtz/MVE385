# -*- coding: utf-8 -*-
"""
Created on Tue Jun 10 21:14:33 2014

@author: mats_j
"""

import os, sys
if sys.version_info < (3,3):    
    print('\nThis skript was developed for running in at least Python 3.3' )
    print( 'Script '+ os.path.basename(sys.argv[0]) +' was exited prematurely')
    exit()

is_Umetrics = os.path.basename(sys.argv[0]) == 'simca.exe'
if is_Umetrics:
    import umetrics, tempfile

import tkinter.filedialog
import tkinter

    
import numpy as np
import MatDataIO

    
def ReadFileList( filename ):
    FileList = open( filename,'r' )
    try:
        ListOfFiles = FileList.read().splitlines()
    finally:
        FileList.close
    return ListOfFiles
        
        
        
def process_input_params():
    # 2 input params
    # Name of file with filenames, output_file_name
    
    if len( sys.argv ) < 3:
        if is_Umetrics:
            scriptpath = os.path.dirname(os.path.realpath(__file__))
            ListOfFiles, file_type = umetrics.impdata.open_file_dialog(filetypes=[('Data file','*.*')],supportedfiletypes=False, multiple=True, initialdir=scriptpath)
            print('file_type:', file_type )
        else:
            print()
            print( 'File parameters missing')
            print( 'Enter: python '+sys.argv[0]+' Name_of_input_file Name_of_output_file')
            print( 'or')
            print()
            print( 'Give input filename(s) manually in the Open file dialog')
            tk_root = tkinter.Tk()
            
            ListOfFiles = tkinter.filedialog.askopenfilenames(multiple=True, title='Please select the input files')
            tk_root.withdraw()      
            if not ListOfFiles:
                sys.exit(1)                
            Output_FileName = os.path.join(os.path.dirname(ListOfFiles[0]), 'ScriptOutputFile.mat')
    else: 
        FilesToProcess = sys.argv[1]
        Output_FileName = sys.argv[2]
        ListOfFiles = ReadFileList( FilesToProcess )
      
    if len(sys.argv) >= 4:
        script_parameters0 = sys.argv[3:]
        script_parameters = []
        for param in script_parameters0: #only keep parameters, not empty strings
           if param: 
               script_parameters.append(param)
    else:
        script_parameters = None
          
    return ListOfFiles, Output_FileName, script_parameters
    
def make_dir_if_absent(d):
    if not os.path.exists(d):
        os.makedirs(d)
    
def print_input_parameters(ScriptName, ListOfFiles, Output_FileName, script_parameters):        
    print()
    print(os.path.basename(ScriptName))
    print()
    print('Input list')
    N = 1
    for current_file in ListOfFiles:
        print(N, '   ', current_file)
        N += 1        
    print()
    print('Output parameter')
    print('   ',Output_FileName)    
    print()
    print('Script parameters')
    if script_parameters:
        print('   ', script_parameters)
    else:
        print('   ', 'None')
    print()
    

""" ---- Main program ---- """
if __name__ == '__main__':

    """ Global settings """
    Version = '2017-12-06'

    debug_operation = False # Force input and output for named files
    """ End global settings """
    
    print()
    print( 'Starting:', os.path.basename(sys.argv[0])) 
    print( ' Version: ', Version)
    print( ' executed with python', sys.version)
    print( )
    sys.stdout.flush()
    
    if debug_operation:
        DbgInputDir = 'C:/1mj2014/Data/Output_repository/2016-11-21/Collect_ges_results/2'
        ListOfFiles = []
        ListOfFiles.append( os.path.join(DbgInputDir,'Collect_ges_results_output_2016-11-21_11.29.26_v4.mat') )
        script_parameters = ''
        
        OutputDbgDir = 'DbgDir01'
        make_dir_if_absent(OutputDbgDir)
        Output_FileName = os.path.join(OutputDbgDir,'Debug_output01.mat')
    else: 
        ListOfFiles, Output_FileName, script_parameters = process_input_params()
    


    if debug_operation:
        print_input_parameters(sys.argv[0], ListOfFiles, Output_FileName, script_parameters)        
    
    for current_file in ListOfFiles:
        print('current_file', current_file)  
    
    
#    MatDataIO.WriteData( Output_FileName, merged_file )
    
    print()
    print( 'Script '+ os.path.basename(sys.argv[0]) +' finished execution')



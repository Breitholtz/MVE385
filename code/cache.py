# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 14:23:57 2016

@author: mats_j
"""

import os, sys
import io
import time
import numpy as np
import scipy
import h5py
import tifffile
from sklearn.cluster import KMeans

try:
    import ReadBIF6 as bif6
    print('Loading development version of ReadBIF6')
except ImportError:
    import ImagePipeline_II.ReadBIF6 as bif6

try:
    import MatDataIO
    print('Loading development version of MatDataIO')
except ImportError:
    import ImagePipeline_II.MatDataIO as MatDataIO
    
try:
    import PreProcFunctions as PreProc
    print('Loading development version of PreProcFunctions')
except ImportError:
    import ImagePipeline_II.PreProcFunctions as PreProc

import zipfile
try:
    import zlib
    zip_compression = zipfile.ZIP_DEFLATED
except:
    zip_compression = zipfile.ZIP_STORED



def get_data3():
    return np.arange(60).reshape([3, 4, 5]).copy()
    
class Timer():
   def __init__(self, timer_ID = ''):
       self.ID = timer_ID

   def __enter__(self):
        print()
        print( 'Start timer', self.ID )
        self.start = time.time()
        
   def __exit__(self, *args):
        consumed_time = time.time() - self.start
        hours = int(np.floor(consumed_time/3600))
        minutes = int(np.floor(consumed_time/60 - hours*60))
        seconds = int(consumed_time - hours*3600 - minutes*60)
        HMS = str(hours)+' h, '+str(minutes).zfill(2)+' m, '+str(seconds).zfill(2)+' s'
        
        print()
        print( self.ID, "time: ", round(consumed_time, 3), 's, --- ', HMS )

              
        

def Get_TextBased_VariableIDs(X_scale0, data_type = 'undef'):
    # The aim with this function is to round to 2 decimals to fit with TOF-SIMS data done earlier than 
    # 2015-04-16 while rounding to 3 decimals when needed for new data
    pref_supply = {}
    pref_supply['MS'] = 'mz_'
    pref_supply['wavenumber'] = ''.join(['v',chr(772)])+'_'
    pref_supply['wavelength'] = 'λ_'
    pref_supply['undef'] = 'Var_'
                  
    if data_type in pref_supply:
        prefix = pref_supply[data_type]
    else:
        prefix = pref_supply['undef'] 
            
    X_scale = np.squeeze(np.asarray(X_scale0))
    # print 'X_scale.shape ', X_scale.shape
    X_scale_IDs = []
    min_diff2dec = np.min(np.abs(np.diff(np.around(X_scale, decimals=2))))
    min_diff3dec = np.min(np.abs(np.diff(np.around(X_scale, decimals=3))))
    min_diff4dec = np.min(np.abs(np.diff(np.around(X_scale, decimals=4))))
    min_diff5dec = np.min(np.abs(np.diff(np.around(X_scale, decimals=5))))
    min_diff6dec = np.min(np.abs(np.diff(np.around(X_scale, decimals=6))))
    
    print( 'min_diff_after_rounding', min_diff2dec, min_diff3dec, min_diff4dec, min_diff5dec, min_diff6dec)
    if min_diff2dec > 0.01:
        for scale_mark in range( 0, X_scale.shape[0] ):            
            X_scale_IDs.append( prefix+ '%.2f' % X_scale[scale_mark])                
    elif min_diff3dec > 0.001:
        for scale_mark in range( 0, X_scale.shape[0] ):
            X_scale_IDs.append( prefix+ '%.3f' % X_scale[scale_mark])
    elif min_diff4dec > 0.0001:
        for scale_mark in range( 0, X_scale.shape[0] ):
            X_scale_IDs.append( prefix+ '%.4f' % X_scale[scale_mark])
    elif min_diff5dec > 0.00001:
        for scale_mark in range( 0, X_scale.shape[0] ):
            X_scale_IDs.append( prefix+ '%.5f' % X_scale[scale_mark])            
    elif min_diff6dec >= 0.000001:
        for scale_mark in range( 0, X_scale.shape[0] ):
            X_scale_IDs.append( prefix+ '%.6f' % X_scale[scale_mark])                       
    else:
        print( 'The X_scale entries are not unique, please redo the x_scale')
        for scale_mark in range( 0, X_scale.shape[0] ):
            scale_entry = prefix+ '%.2f' % X_scale[scale_mark] 
            if scale_entry in X_scale_IDs:
                 X_scale_IDs.append(scale_entry+'(dup)')
            else:
                X_scale_IDs.append(scale_entry)
    
    # print 'X_scale_IDs to be returned', X_scale_IDs
    return X_scale_IDs


def neutralFunc(X):
    return X

def log10_eps(X):
    eps = 0.5
    return np.log10(X+eps)

def getNpIndices( booleanArray ):
    indices = np.where(booleanArray==True)[0]
    return indices


class HyperSpectralCache:

    def __init__(self, Cache_file_name):        
        self.cache_file_handle = h5py.File(Cache_file_name, 'a' )
        self.transformation = neutralFunc
        self.transformation2 = neutralFunc
        
    def close(self, is_DeleteCache_on_close=False):
        currentCache_FileName = self.cache_file_handle.filename
        self.cache_file_handle.close()
        if is_DeleteCache_on_close:
            os.remove(currentCache_FileName)
            
    def CacheCreateError(self, DataSetName, RecordName):
        ErrStr1 = '*** Cache create error\n'
        ErrStr2 = '    Record: '+RecordName+', could not be created a second time\n'
        ErrStr3 = '    with the same name in the DataSet: '+DataSetName
        raise ValueError(ErrStr1+ErrStr2+ErrStr3)
        
    def enter_Data(self, DataSetName, RecordName, mat_data):
        if RecordName in self.get_RecordNames(DataSetName):
            self.CacheCreateError(DataSetName, RecordName)
        else:
#            #print('enter_Data', DataSetName, RecordName, 'mat_data.ndim', mat_data.ndim )
            dset1str = '/'+DataSetName+'/'+RecordName
            dset1 =self.cache_file_handle.create_dataset(dset1str, data=mat_data)
            dset1.attrs[ 'MATLAB_class' ] = 'double'
        

    def enter_IDs( self, DataSetName, RecordName, input_list0 ):
        # Write a list of strings <input_list> for a matlab variable on the hdf5_file_handle
        # with the variable name <RecordName> in Matlab V7.3 binary file format as obtained from the
        # 'save filename matrixname .... -v7.3' command in Matlab
        if RecordName in self.get_RecordNames(DataSetName):
            self.CacheCreateError(DataSetName, RecordName)
        else:            
            """
            Take care of the case when there is a single string as input rather than a list of strings"""
            if isinstance(input_list0, str):
                input_list = [input_list0]
            else:
                input_list = input_list0
                
            ID_mat = self.Mk_Matlab7_3_text_matrix( input_list )
            dset2str = '/'+DataSetName+'/'+RecordName
            dset2 = self.cache_file_handle.create_dataset(dset2str, data=ID_mat)
            dset2.attrs[ 'MATLAB_class' ] = 'char'
            dset2.attrs[ 'MATLAB_int_decode' ] = 2
        
        
    def is_text(self, DataSetName, RecordName):
        dset2record = '/'+DataSetName+'/'+RecordName
        return self.cache_file_handle[dset2record].attrs[ 'MATLAB_class' ] == 'char'
    
    def is_Logical(self, DataSetName, RecordName):
        dset2record = '/'+DataSetName+'/'+RecordName
        return self.cache_file_handle[dset2record].attrs[ 'MATLAB_class' ] == 'logical'
    
    def is_Data(self, DataSetName, RecordName):
        dset2record = '/'+DataSetName+'/'+RecordName
        return self.cache_file_handle[dset2record].attrs[ 'MATLAB_class' ] == 'double'
        
        
    def enter_Logical(self, DataSetName, RecordName, boolean_array):
        if RecordName in self.get_RecordNames(DataSetName):
            self.CacheCreateError(DataSetName, RecordName)
        else:
            dset3str = '/'+DataSetName+'/'+RecordName
            mat_logical = np.asarray(boolean_array, dtype=np.uint8)
            dset3 =self.cache_file_handle.create_dataset(dset3str, data=mat_logical)
            dset3.attrs[ 'MATLAB_class' ] = 'logical'
            dset3.attrs[ 'MATLAB_int_decode' ] = 1

            
    def update_Data(self, DataSetName, RecordName, mat_data):
        self.remove_Record(DataSetName, RecordName)
        self.enter_Data(DataSetName, RecordName, mat_data)
            
    def update_IDs(self, DataSetName, RecordName, input_list0):
        self.remove_Record(DataSetName, RecordName)
        self.enter_IDs( DataSetName, RecordName, input_list0 )

    def update_Logical(self, DataSetName, RecordName, boolean_array):
        self.remove_Record(DataSetName, RecordName)
        self.enter_Logical(DataSetName, RecordName, boolean_array)
       
    def remove(self, DataSetName):
        del self.cache_file_handle[DataSetName]

    def remove_Record(self, DataSetName, RecordName):
        if RecordName in self.get_RecordNames(DataSetName):
            dset2str = '/'+DataSetName+'/'+RecordName
            del self.cache_file_handle[dset2str]

    def copy_Record(self, srcDataSetName, destDataSetName, RecordName):
        if self.is_text(srcDataSetName, RecordName):
            self.enter_IDs(destDataSetName, RecordName, self.get_IDs(srcDataSetName, RecordName))
        elif self.is_Logical(srcDataSetName, RecordName):
            self.enter_Logical(destDataSetName, RecordName, self.get_Logical(srcDataSetName, RecordName))
        elif self.is_Data(srcDataSetName, RecordName):
            self.enter_Data(destDataSetName, RecordName, self.get_Data(srcDataSetName, RecordName))
                                    
        
    def create_EmptyArray(self, DataSetName, RecordName, tuple_of_sizes):
        dset2str = '/'+DataSetName+'/'+RecordName
        dset = self.cache_file_handle.create_dataset(dset2str, tuple_of_sizes, dtype=np.uint32) #Default type is 32-bit floating point
        return dset
        
    def get_ListOfDataSets(self):
        return list(self.cache_file_handle.keys())
    
        
    def get_RecordNames(self, DataSetName):
        if DataSetName in self.get_ListOfDataSets(): 
            dset2str = '/'+DataSetName
            return list(self.cache_file_handle[dset2str].keys())
        else:
            return []
        
    def get_Data(self, DataSetName, RecordName):
        dset2str = '/'+DataSetName+'/'+RecordName
        return self.cache_file_handle[dset2str]
    
    def get_DataSize(self, DataSetName, RecordName):
        return self.get_Data(DataSetName, RecordName).shape
    
    def get_Logical(self, DataSetName, RecordName):
        return self.get_Data(DataSetName, RecordName)
    
    def get_binned_ImageSize(self, DataSetName, bin_size_power=0):
        rows, cols, sp_len = self.get_Data(DataSetName, 'IMAGE').shape
        sz_divisor = (2**bin_size_power)
        return rows//sz_divisor, cols//sz_divisor, sp_len            
    
    def get_Name_RawDataSet(self, DataSetName):
        currentRecords = self.get_RecordNames(DataSetName)
        if 'Raw_data' in currentRecords:
            Name_RawDataSet = self.get_IDs(DataSetName, 'Raw_data')[0]
        else:
            Name_RawDataSet = DataSetName
        return Name_RawDataSet
    
    def get_SourceFilePath(self, DataSetName):
        currentRecords = self.get_RecordNames(DataSetName)
        if 'SOURCE_FILE' in currentRecords:
            SourceFilePath = self.get_IDs(DataSetName, 'SOURCE_FILE')[0]
        else:
            SourceFilePath = 'undef'
        return SourceFilePath
        
        
        
    def get_IDs(self, DataSetName, RecordName):
        # print('Get_IDs', DataSetName, RecordName )
        dset2str = '/'+DataSetName+'/'+RecordName         
        if (self.cache_file_handle[dset2str].attrs['MATLAB_class'] == 'char') or \
           (self.cache_file_handle[dset2str].attrs['MATLAB_class'] == b'char'):
            mat_chars = self.cache_file_handle[dset2str][:].T
            matlist = self.Rd_Matlab7_3_text_matrix(mat_chars)
            return matlist
        else:
            return [RecordName+ ' did not contain text IDs']


    def get_sorted_IDs(self, DataSetName, RecordName, sort_order=1):
        ID_list = self.get_IDs(DataSetName, RecordName)
        if sort_order == 0: #Get list of as many number as there are variables
            property_list = list(self.get_SpectrumOrder(DataSetName, 'IMAGE'))
        if sort_order == 1: #sum of variable
#            SpectralSum = self.get_SpectralSum(DataSetName, 'IMAGE')
#            print('SpectralSum', SpectralSum.shape)
            property_list = list(self.get_SpectralSum(DataSetName, 'IMAGE'))
            
        elif sort_order == 2: #max of variable
            property_list = list(self.get_SpectralMax(DataSetName, 'IMAGE'))
            
        if len(ID_list) == len(property_list):
            paired = []
            paired.append(property_list)
            paired.append(ID_list)

            property_pairs = list(sorted(map(list, zip(*paired)), reverse=True))            
            sorted_by_properties = list((map(list, zip(*property_pairs))))
#            print('property_pairs', property_pairs)
            
        return sorted_by_properties[1] 

        
    def get_TotIon_PercentileSelected(self, DataSetName, RecordName, percentile, bin_size_power=0):
        """
        get_TotIon_PercentileSelected -- return a boolean 2D array marking the spectra above an input percentile
        This one may be quicker using get_TotIon_PercentileSelected followed by getUnfolded_IncludedPixels
        """
        #Done - Take care of binning here when desired for algorithm testing
        #TODO - alt take care of binning after selection on full resolution
        if bin_size_power > 0:
            Tot_ion_img = self.get_BinnedSlice(self.get_ImageSum(DataSetName, RecordName ), bin_size_power)
        else:
            Tot_ion_img = self.get_ImageSum(DataSetName, RecordName )
        high_percentil_score = scipy.stats.scoreatpercentile( np.ravel(Tot_ion_img), per=percentile)
        pixel_selection = Tot_ion_img >= high_percentil_score
        return pixel_selection
    

    def get_TotIonSelection(self, DataSetName, RecordName, percentile):
        """
        get_TotIonSelection -- return a hyperspectral image with only the spectra above an input percentile
        This one may be slower than working on unfolded spectra using 
            get_TotIon_PercentileSelected followed by getUnfolded_IncludedPixels     
        """
        hysp_image = self.get_Data(DataSetName, RecordName)
        hsi_selection = np.zeros(hysp_image.shape)
        Tot_ion_img = np.sum(hysp_image, axis=2)
        high_percentil_score = scipy.stats.scoreatpercentile( np.ravel(Tot_ion_img), per=percentile)
        pixel_selection = Tot_ion_img >= high_percentil_score
        pixel_3D_selectionxAll = np.dstack([pixel_selection for i in range(hysp_image.shape[2])])
        hsi_selection[:,:,:][pixel_3D_selectionxAll] = hysp_image[:,:,:][pixel_3D_selectionxAll]
        return hsi_selection, pixel_selection
        
    
    
    def get_binned3Dcube(self, DataSetName, RecordName, bin_size_power=0):
        trace = False
        hysp_image = self.get_Data(DataSetName, RecordName)
        (rows, cols, spectral_dim) = hysp_image.shape
        if bin_size_power < 0:
            print('Binning can only be done by positive numbers')
        elif 2 ** bin_size_power > np.min((rows, cols)):
            print('The bin size exceeds the smallest dimension of the images')
        elif bin_size_power == 0:
            return hysp_image
        else:           
            # only power of 2 allowed
            bin_size = 2 ** bin_size_power
            if trace:
                print()
                print('bin_size', bin_size)
            binned_hysp_image = np.zeros((hysp_image.shape[0] // bin_size, hysp_image.shape[1] // bin_size, hysp_image.shape[2]) )
            for i in range(binned_hysp_image.shape[0]):
                x_slice = np.sum(hysp_image[i*bin_size:(i+1)*bin_size, :, :], axis=0)
        #            print('x_slice.shape',x_slice.shape)
                y_binned_x_slice = np.reshape(x_slice, (x_slice.shape[0]//bin_size, bin_size, x_slice.shape[1] ))
        #            print('y_binned_x_slice.shape', y_binned_x_slice.shape)
                x_binned_x_slice = np.sum(y_binned_x_slice, axis=1)
        #            print('x_binned_x_slice.shape', x_binned_x_slice.shape)
                binned_hysp_image[i,:,:] = x_binned_x_slice
            return binned_hysp_image
            

    def get_binned_3Dslice(self, DataSetName, RecordName, i, bin_size_power=0, img_slice_direction=2 ):
        if img_slice_direction != 2:
            print('Currently takes only slices with the slice index in axis 2')
        else:
            if bin_size_power == 0:
                return self.get_3Dslice(DataSetName, RecordName, i, img_slice_direction )
            elif bin_size_power < 0:
                print('Binning can only be done by positive numbers')
            else:
                hysp_image = self.get_Data(DataSetName, RecordName)
                (rows, cols, spectral_dim) = hysp_image.shape                
                if 2 ** bin_size_power > np.min((rows, cols)):
                    print('The bin size exceeds the smallest dimension of the images')
                else:
                    bin_size = 2 ** bin_size_power
                    binned_hysp_img_slice = np.zeros((hysp_image.shape[0] // bin_size, hysp_image.shape[1] // bin_size) )
                    for yi in range(binned_hysp_img_slice.shape[0]):
                        # Summera alla x-lager inom bin
                        x_slice = np.sum(hysp_image[yi*bin_size:(yi+1)*bin_size, :, i], axis=0)
                        print('x_slice.shape',x_slice.shape)
                        # Vik ut alla bins i axis 1 (x) för att kunna summera dom med np.sum nedan
                        y_binned_x_slice = np.reshape(x_slice, (x_slice.shape[0]//bin_size, bin_size, 1 ))
                        print('y_binned_x_slice.shape', y_binned_x_slice.shape)
                        x_binned_x_slice = np.sum(y_binned_x_slice, axis=1)
                        print('x_binned_x_slice.shape', x_binned_x_slice.shape)
                        binned_hysp_img_slice[yi,:] = np.squeeze(x_binned_x_slice)
                        
                    return binned_hysp_img_slice
            
        
    def get_3Dslice(self, DataSetName, RecordName, i, img_slice_direction=2 ):
        dset2str = '/'+DataSetName+'/'+RecordName
        s = None
        if img_slice_direction == 2:
            s = self.cache_file_handle[dset2str][:,:,i]
        elif img_slice_direction == 1:
            s = self.cache_file_handle[dset2str][:,i,:]
        elif img_slice_direction == 0:
            s = self.cache_file_handle[dset2str][i,:,:]
        else:
            print('axis not in 3D range')
        return s
    
    def set_Transformation(self, transformfunc):
        self.transformation = transformfunc
        
    def set_Transformation2(self, transformfunc):
        self.transformation2 = transformfunc

    def get_Trans_3Dslice(self, DataSetName, RecordName, slice_number, img_slice_direction=2 ):                
        S = self.get_3Dslice(DataSetName, RecordName, slice_number, img_slice_direction)      
        return self.transformation2(self.transformation(S))
    
    def get_Total_3DSlice_MinMax(self, slice_number):
        DataSets = self.get_ListOfDataSets()
        is_first = True 
        for Dname in DataSets:
            D_slice = self.get_3Dslice(Dname, 'IMAGE', slice_number)
            if is_first:
                total_min = np.nanmin(D_slice)
                total_max = np.nanmax(D_slice)
                is_first = False
            else:                
                total_min = min(total_min, np.nanmin(D_slice))
                total_max = max(total_min, np.nanmax(D_slice))
        return total_min, total_max
    

    def get_percentiles_MinMax(self, AllSlices, lower_PerMilleTile, upper_PerMilleTile):
        lower_percentile = 0.1*lower_PerMilleTile
        upper_percentile = 0.1*upper_PerMilleTile
        no_NaNs = np.isfinite(AllSlices)       
        NoNaNpixels = AllSlices[no_NaNs]
        if NoNaNpixels.shape[0] > 0:
            if (upper_percentile < 100) and (upper_percentile > 0):
                overall_max = scipy.stats.scoreatpercentile( NoNaNpixels, per=upper_percentile)
            else:
                overall_max = np.nanmax(AllSlices)
            
            if (lower_percentile < 100) and (lower_percentile > 0):
                overall_min = scipy.stats.scoreatpercentile( NoNaNpixels, per=lower_percentile)
            else:
                overall_min = np.nanmin(AllSlices)
        else:
            overall_min = None
            overall_max = None
        return overall_min, overall_max
    

    def get_One_3DSlice_MinMax_from_percentiles(self, Dname, slice_number, lower_PerMilleTile, upper_PerMilleTile ):
        OneSlice = np.ravel(self.get_3Dslice(Dname, 'IMAGE', slice_number))
        local_min, local_max = self.get_percentiles_MinMax(OneSlice, lower_PerMilleTile, upper_PerMilleTile)
        return local_min, local_max
    
    def get_OneTrans_3DSlice_MinMax_from_percentiles(self, Dname, slice_number, lower_PerMilleTile, upper_PerMilleTile ):
        OneSlice = self.transformation2(self.transformation(np.ravel(self.get_3Dslice(Dname, 'IMAGE', slice_number))))
        local_min, local_max = self.get_percentiles_MinMax(OneSlice, lower_PerMilleTile, upper_PerMilleTile)
        return local_min, local_max

    
    def get_Overall_3DSlice_MinMax_from_percentiles(self, Dmatch, slice_number, lower_PerMilleTile, upper_PerMilleTile ):
        is_first = True
        match_num_of_slices = self.get_Data( Dmatch, 'IMAGE').shape[2]
        DataSets = self.get_ListOfDataSets()
        for Dname in DataSets:
            num_of_slices = self.get_Data( Dname, 'IMAGE').shape[2]
            if num_of_slices == match_num_of_slices:
                if is_first:                
                    AllSlices = np.ravel(self.get_3Dslice(Dname, 'IMAGE', slice_number))
                    is_first = False
                else:
                    NewSlice = np.ravel(self.get_3Dslice(Dname, 'IMAGE', slice_number))       
                    AllSlices = np.concatenate( (AllSlices, NewSlice) )
                    
        overall_min, overall_max = self.get_percentiles_MinMax(np.ravel(AllSlices), lower_PerMilleTile, upper_PerMilleTile)
        return overall_min, overall_max
            

    def get_BinnedSlice(self, hysp_slice, bin_size_power):
        """
        get_BinnedSlice(hysp_slice, bin_size_power):
        
        hysp_slice:     input 2D non-binned slice 
        bin_size_power: the exponent of the desired binning        
        output:         the binned 2D slice from the input
        """ 
        trace = False
        rows, cols = hysp_slice.shape                
        if 2 ** bin_size_power > np.min((rows, cols)):
            print('get_BinnedSlice:','The bin size exceeds the smallest dimension of the images')
        else:
            bin_size = 2 ** bin_size_power
            binned_hysp_img_slice = np.zeros((rows // bin_size, cols // bin_size) )
            if trace:
                    print('binned_hysp_img_slice.shape', binned_hysp_img_slice.shape)
            for yi in range(binned_hysp_img_slice.shape[0]):
                # Summera alla x-lager inom bin
                x_slice = np.sum(hysp_slice[yi*bin_size:(yi+1)*bin_size, :], axis=0)
                if trace:
                    print('x_slice.shape',x_slice.shape)
                # Vik ut alla bins i axis 1 (x) för att kunna summera dom med np.sum nedan
                y_binned_x_slice = np.reshape(x_slice, (x_slice.shape[0]//bin_size, bin_size))
                if trace:
                    print(yi, 'y_binned_x_slice.shape', y_binned_x_slice.shape)
                x_binned_x_slice = np.sum(y_binned_x_slice, axis=1)
                if trace:
                    print(yi, 'x_binned_x_slice.shape', x_binned_x_slice.shape)
                binned_hysp_img_slice[yi,:] = x_binned_x_slice
                
            return binned_hysp_img_slice


    def get_ImageSum(self, DataSetName, RecordName, img_slice_direction=2 ):
        dset2str = '/'+DataSetName+'/'+RecordName
        tot_sum = np.sum(self.cache_file_handle[dset2str], axis=img_slice_direction)
        return tot_sum
        
    def get_SpectralSum(self, DataSetName, RecordName, img_slice_direction=2 ):
        dset2str = '/'+DataSetName+'/'+RecordName
        if img_slice_direction == 2:
            over_axes = (0,1)
        elif img_slice_direction == 1:
            over_axes = (0,2)
        elif img_slice_direction == 0:
            over_axes = (1,2)            
        spectrum = np.sum(self.cache_file_handle[dset2str], axis=over_axes)
        return spectrum
    
    def get_SpectralAvg(self, DataSetName, RecordName, img_slice_direction=2 ):
        dset2str = '/'+DataSetName+'/'+RecordName
        if img_slice_direction == 2:
            over_axes = (0,1)
        elif img_slice_direction == 1:
            over_axes = (0,2)
        elif img_slice_direction == 0:
            over_axes = (1,2)            
        spectrum = np.mean(self.cache_file_handle[dset2str], axis=over_axes)
        return spectrum
    
    def get_Spectral_numeric_xaxis(self, DataSetName):
        return self.get_Data(DataSetName, 'VARID2')
    
    def get_SpectralMax(self, DataSetName, RecordName, img_slice_direction=2 ):
        dset2str = '/'+DataSetName+'/'+RecordName
        if img_slice_direction == 2:
            over_axes = (0,1)
        elif img_slice_direction == 1:
            over_axes = (0,2)
        elif img_slice_direction == 0:
            over_axes = (1,2)            
        spectrum = np.nanmax(self.cache_file_handle[dset2str], axis=over_axes)
        return spectrum
    
    def get_SpectrumOrder(self, DataSetName, RecordName):
        dset2str = '/'+DataSetName+'/'+RecordName
        spectrumOrder = np.arange(0, self.cache_file_handle[dset2str].shape[2]) 
        reversed_spectrumOrder = spectrumOrder[::-1] #High numbers first
        return reversed_spectrumOrder
    
    def get_TOF_SIMS_reference_spectrum(self, DataSetName, binning=0, 
                                        is_Poisson_scaling=True, noise_threshold=0):
        """
        The default setting, noise_threshold=0, removes all pixels with the total ion count
        of 0 from the calculation of the reference mean spectrum. Thus if backround was 
        removed and set to zero, these pixesl will not contribute to the mean intensities
        of the reference spectrum.
        """
    

        def get_Ref_Spectrum(px_sel, FullFileName, img, x_scale, is_Poisson_scaling):
            """
            px_sel             :Selection of pixels as boolean 2D array
            FullFileName       :The filename of the reference image including full path
            img                :The raw 3D hyperspectal image
            x_scale            :The mass-scale of the hyperspectal image
            is_Poisson_scaling :The boolean input variable fro control of Poisson scaling of variables
            """
            trace = False
            #    with hsc.Timer('makes selection'):
            if trace:
                print('img.shape', img.shape) 
            hsi_selection = np.ones(img.shape)*np.NaN
            pixel_3D_selectionxAll = np.dstack([px_sel for i in range(img.shape[2])])
            hsi_selection[:,:,:][pixel_3D_selectionxAll] = img[:,:,:][pixel_3D_selectionxAll]
    
            S = {}
            S['FileName'] = os.path.basename(FullFileName)
            S['PathName'] = os.path.dirname(FullFileName)
            if x_scale.ndim > 1:
                S['x'] = np.squeeze(np.asarray(x_scale))
            else:
                S['x'] = x_scale
    
            if is_Poisson_scaling:
                Poiss_spectral_average = np.nanmean(img, axis=(0,1))            
                poiss_w = PreProc.Poisson_weights( Poiss_spectral_average, True )
                Poiss_scaled_img = np.multiply( hsi_selection, poiss_w)              
                S['Spectrum'] = np.nanmean(Poiss_scaled_img, axis=(0,1))
                S['is_Poisson_scaling'] = True
            else:
                S['Spectrum'] = np.nanmean(hsi_selection, axis=(0,1))
                S['is_Poisson_scaling'] = False   
            return S

    
        totImg = self.get_ImageSum(DataSetName, 'IMAGE' )
#        all_spectra = totImg.size
        if noise_threshold <= 0:
            selection_threshold = 0.0
        else:
            selection_threshold = noise_threshold
        spectral_selection = (totImg > selection_threshold)
        if 'LAST_FILE' in self.get_RecordNames(DataSetName):
            InpFname = self.get_IDs( DataSetName, 'LAST_FILE')[0]
        else:
            InpFname = self.get_IDs( DataSetName, 'SOURCE_FILE')[0]
        Hsi = self.get_binned3Dcube( DataSetName, 'IMAGE', binning)
        Hsi_x_scale = self.get_Data(DataSetName, 'VARID2')[:]
        Ref_spectrum = get_Ref_Spectrum(spectral_selection, InpFname, Hsi, Hsi_x_scale, is_Poisson_scaling)
        return Ref_spectrum



    def is_loaded(self, FileName):        
        tst_DataSetName = os.path.basename(os.path.splitext(FileName)[0])
        return tst_DataSetName in self.get_ListOfDataSets()
    

    def translate_to_DataSet_name(self, FullPathFileName):
        if (os.path.splitext(FullPathFileName)[1] == '.zip'):
            zippedFileName = self.get_ZippedBIF6_filenames(FullPathFileName)[0] #Assuming there is only one zipped BIF6 file
            DataSet_name = os.path.splitext(os.path.basename(zippedFileName))[0]
        elif (os.path.splitext(FullPathFileName)[1] == '.mat'):
            DataSet_name = os.path.splitext(os.path.basename(FullPathFileName))[0].split('-v73',1)[0]
        else:
            DataSet_name = os.path.splitext(os.path.basename(FullPathFileName))[0]
        return DataSet_name


    def get_ZippedBIF6_filenames(self, zipped_fname):
        trace = True
        UnZippedFileNames = []
        is_zipped = zipfile.is_zipfile(zipped_fname)
        if not is_zipped:
            print('get_ZippedBIF6_filenames', zipped_fname, 'does not appear to be a zip-file')
        else:
            zf_obj = zipfile.ZipFile(zipped_fname, 'r')
            try:
                if trace:
                    print()
                    print( 'zf_obj.namelist()', zf_obj.namelist() )
                
                for InputF in zf_obj.namelist():
                    if (os.path.splitext(InputF)[1] == '.BIF6'):
                        UnZippedFileNames.append(InputF)
            finally:
                zf_obj.close()

        if trace:        
            print('get_ZippedBIF6_filenames returned UnZippedFileNames', UnZippedFileNames)
        return UnZippedFileNames        


    def load_one_ZippedBIF6_file(self, zipped_fname, ClassNumber=1):
        is_timing = False
        UnZippedFileNames = self.get_ZippedBIF6_filenames(self, zipped_fname)
        if UnZippedFileNames:
            zf_obj2 = zipfile.ZipFile(zipped_fname, 'r')
            try:
                one_bif6_file_name = UnZippedFileNames[0]
                if is_timing:
                    with Timer('Unzipping'):                
                        bif6_file = io.BytesIO(zf_obj2.read(one_bif6_file_name))
                else:
                    bif6_file = io.BytesIO(zf_obj2.read(one_bif6_file_name))
                try:
                    if not bif6.Read_FileID( bif6_file ):
                        DataSetName = ''
                        print('*** Warning', os.path.basename(one_bif6_file_name), 'was not recognized as a BIF6 file')
                    else:
                        DataSetName = self.process_BIF6_file(bif6_file, one_bif6_file_name, zipped_fname, ClassNumber)
                finally:
                    bif6_file.close()
            finally:
                zf_obj2.close()    
        return DataSetName
        
    
    def load_ZippedBIF6_files(self, zipped_fname, ClassNumber=1):
        trace = True
        is_timing = False
        DataSetNames = []
        is_zipped = zipfile.is_zipfile(zipped_fname)
        if not is_zipped:
            print('load_ZippedBIF6_files', zipped_fname, 'does not appear to be a zip-file')
        else:
            zf = zipfile.ZipFile(zipped_fname, 'r')
            try:
                if trace:
                    print()
                    print( 'zf.namelist()', zf.namelist() )
                for one_bif6_file_name in zf.namelist():
                    if is_timing:
                        with Timer('Unzipping'):                
                            bif6_file = io.BytesIO(zf.read(one_bif6_file_name))
                    else:
                        bif6_file = io.BytesIO(zf.read(one_bif6_file_name))
                    try:
                        if not bif6.Read_FileID( bif6_file ):
                            print('*** Warning', os.path.basename(one_bif6_file_name), 'was not recognized as a BIF6 file')
                        else:
                            DataSetName = self.process_BIF6_file(bif6_file, one_bif6_file_name, zipped_fname, ClassNumber)
                            if DataSetName:
                                DataSetNames.append(DataSetName)
                    finally:
                        bif6_file.close()
            finally:
                zf.close()    
        return DataSetNames
                    

    def load_BIF6_file(self, bif6_file_name, ClassNumber=1):
        DataSetName = []              
        bif6_file = open( bif6_file_name, 'rb')
        try:
            if not bif6.Read_FileID( bif6_file ):
                print('*** Warning', os.path.basename(bif6_file_name), 'was not recognized as a BIF6 file')
                DataSetName.append('')
            else:
                DataSetName.append(self.process_BIF6_file(bif6_file, bif6_file_name, bif6_file_name, ClassNumber))
        finally:
            bif6_file.close()
        return DataSetName
        

    def load_HDF5_mat_file(self, FileName):

        DataSetNames = []
        DataSetNames.append( self.Read_one_file_with_unfolded_spectra(FileName) )
        return DataSetNames
    

    def load_any_TOF_SIMS_files(self, InputFiles0):
        All_input_DataSets = []
        if isinstance(InputFiles0, str):
            InputFiles = [InputFiles0]
        else:
            InputFiles = InputFiles0
        for InputF in InputFiles:
            if not self.is_loaded(InputF):
                if (os.path.splitext(InputF)[1] == '.BIF6'):
                    DataSetNames = self.load_BIF6_file(InputF)                    
                elif (os.path.splitext(InputF)[1] == '.zip') and ('BIF6' in InputF):
                    DataSetNames = self.load_ZippedBIF6_files(InputF)
                elif (os.path.splitext(InputF)[1] == '.mat') and ('-v73' in InputF):
                    DataSetNames = self.load_HDF5_mat_file(InputF)
                else:
                    print()
                    print(InputF, '\n was not loaded as it was not recognized')
            else:
                print('Info:', os.path.basename(InputF), 'was already loaded')
            All_input_DataSets.extend(DataSetNames)
        return All_input_DataSets
        

    def load_tiff_stack_file(self, FileName, IPL_version):
        Dname = None
        try:
            tiff_stack = tifffile.imread(FileName)
            Dname = os.path.basename(os.path.splitext(FileName)[0])
            num_of_images, img_Y_size, img_X_size = tiff_stack.shape
            Images_full_array = np.zeros( (img_Y_size, img_X_size, num_of_images), dtype=np.float32 )
            for i in range(num_of_images):
                Images_full_array[:,:,i] = tiff_stack[i,:,:]
                           
            x_scale = np.arange(num_of_images) +1
            
            self.enter_IDs(Dname, 'SOURCE_FILE', [FileName])
            self.enter_IDs(Dname,'META_INFO', [os.path.basename(sys.argv[0])+' '+IPL_version] )
            self.enter_IDs(Dname, 'VARID1', Get_TextBased_VariableIDs(x_scale))
            self.enter_Data(Dname, 'VARID2', x_scale)
            self.enter_Data(Dname, 'IMAGE', Images_full_array)
        finally:
            return Dname
        
    def ColumnVector(self, v):
        if v.ndim == 1:
            return np.mat(v).T
        elif (v.ndim == 2) and (v.shape[0] == 1):
            return v.T
        elif (v.ndim == 2) and (v.shape[1] == 1):
            return v
        else:
            print('The input was not a vector')
            return None
    
    
    def load_scores(self, srcDataSetName, prefix, y_index, x_index, T, component_names=[], loadings=np.array([])):
        if T.ndim == 1:
            image, included_pixels = self.convert_UnfoldedData_to_HySpImage(y_index, x_index, self.ColumnVector(T))
        else:
            image, included_pixels = self.convert_UnfoldedData_to_HySpImage(y_index, x_index, T)
        destDataSetName = prefix+srcDataSetName
        self.enter_Data(destDataSetName, 'IMAGE', image)
        if 'SOURCE_FILE' in self.get_RecordNames(srcDataSetName):
            self.enter_IDs(destDataSetName, 'SOURCE_FILE', self.get_IDs(srcDataSetName, 'SOURCE_FILE'))
        else:
            print('load_scores', 'Warning:', "key 'SOURCE_FILE' is missing"  )
        self.enter_IDs(destDataSetName,'META_INFO', [os.path.basename(sys.argv[0])] )
        self.enter_IDs(destDataSetName,'Raw_data', [srcDataSetName] )
        self.enter_IDs(destDataSetName,'Parent_DataSet', [srcDataSetName] )
        
        if T.ndim == 1:
            components = 1
        else:
            components = T.shape[1]
        if component_names:
            self.enter_IDs(destDataSetName, 'VARID1', component_names)
        else:    
            auto_names = []
            for j in range(components):
                comp_name = 'comp_'+str(j+1).zfill(2)
                auto_names.append(comp_name)
            self.enter_IDs(destDataSetName, 'VARID1', auto_names)
        
        numeric_components = np.arange(components)
        self.enter_Data(destDataSetName, 'VARID2', numeric_components)
        
        """ Handle loadings if they exist """
        if np.size(loadings):
            self.enter_Data(destDataSetName, 'LOADINGS', loadings)
            if 'VARID1' in self.get_RecordNames(srcDataSetName):
                loadings_x_ids = self.get_IDs(srcDataSetName, 'VARID1') 
            if 'VARID2' in self.get_RecordNames(srcDataSetName):
                loadings_x_scale = self.get_Data(srcDataSetName, 'VARID2')
            self.enter_IDs(destDataSetName, 'LOADINGS_X1', loadings_x_ids)
            self.enter_Data(destDataSetName, 'LOADINGS_X2', loadings_x_scale)
    
        return destDataSetName
    

    def load_derived_Unfolded_HySp_data(self, srcDataSetName, derivedUnfData, y_index, x_index, prefix):
        if derivedUnfData.ndim == 1:
            image, included_pixels = self.convert_UnfoldedData_to_HySpImage(y_index, x_index, self.ColumnVector(derivedUnfData))
        else:
            image, included_pixels = self.convert_UnfoldedData_to_HySpImage(y_index, x_index, derivedUnfData)
        destDataSetName = prefix+srcDataSetName
        self.enter_Data(destDataSetName, 'IMAGE', image)
        if 'SOURCE_FILE' in self.get_RecordNames(srcDataSetName):
            self.enter_IDs(destDataSetName, 'SOURCE_FILE', self.get_IDs(srcDataSetName, 'SOURCE_FILE'))
        else:
            print('load_derived_Unfolded_HySp_data', 'Warning:', "key 'SOURCE_FILE' is missing"  )
        self.enter_IDs(destDataSetName,'META_INFO', [os.path.basename(sys.argv[0])] )
        self.enter_IDs(destDataSetName,'Raw_data', [srcDataSetName] )
        self.enter_IDs(destDataSetName,'Parent_DataSet', [srcDataSetName] )

        for entry in self.get_RecordNames(srcDataSetName):
            if entry not in ['IMAGE', 'SOURCE_FILE', 'META_INFO', 'Raw_data', 'Parent_DataSet']:
                self.copy_Record(srcDataSetName, destDataSetName, entry)
        
        return destDataSetName
    

    def load_IPL_binary_file(self, FileName):
        trace = False
        IPL_pred = MatDataIO.ReadData(FileName)
        for key in IPL_pred:
            if key[0:7] == 'RawImg_':
                self.enter_Data(key, 'IMAGE', IPL_pred[key])
                self.enter_IDs(key, 'SOURCE_FILE', [FileName])
                self.enter_IDs(key, 'VARID1', IPL_pred['VARID1'])
            elif key[0:8] == 'FlatImg_':
                if IPL_pred[key].ndim ==2:
                    hysp_layer = np.zeros((IPL_pred[key].shape[0], IPL_pred[key].shape[1], 1))
                    hysp_layer[:,:,0] = IPL_pred[key]
                    self.enter_Data(key, 'IMAGE', hysp_layer)
                else:
                    self.enter_Data(key, 'IMAGE', IPL_pred[key])
                self.enter_IDs(key, 'SOURCE_FILE', [FileName])
                self.enter_IDs(key, 'VARID1', IPL_pred['VARID1'])
            elif trace:
                print('load_IPL_binary_file', 'Did not handle key:',key,'in an ImagePipeline_I binary file')
            
                
                                
                
    def process_BIF6_file(self, bif6_file, one_bif6_file_name, source_filename, ClassNumber):
        trace = False
        Sample_name = os.path.splitext(os.path.basename(one_bif6_file_name))[0]
        if Sample_name in self.get_ListOfDataSets():
            return None
        else:
            num_of_images, img_X_size, img_Y_size = bif6.Read_FileInfo( bif6_file )
            
#            IonImages = self.create_EmptyArray(Sample_name, 'IMAGE', (img_Y_size, img_X_size, num_of_images) )
            
            # bif6_file type for image is uint32
            IonImages_full_array = np.zeros( (img_Y_size, img_X_size, num_of_images), dtype=np.uint32 )
            
            PeakID_numeric     = np.zeros( (num_of_images)) # mean of upper and lower
            IONTOF_Image_Index = np.zeros( (num_of_images)) # IONTOF Image Index
            PeakBegin          = np.zeros( (num_of_images)) # lower mass
            PeakEnd            = np.zeros( (num_of_images)) # upper mass
            PeakCenter         = np.zeros( (num_of_images)) # center of mass, do not use for ID
            with Timer('Img to cache'):
                if trace: 
                    print('IMAGE')
                for img_no in range(0, num_of_images):
        #            print('.',end='')
        #            sys.stdout.flush()
#                    print(img_no,'of',num_of_images)
                    ImageIndex, Center_mass, lower_mass, upper_mass = bif6.Read_ImageInfo( bif6_file )                           
        
                    PeakID_numeric[img_no] = (upper_mass + lower_mass) / 2.0 # This average is more stable than Center_mass
                    IONTOF_Image_Index[img_no] = ImageIndex
                    PeakBegin[img_no] = lower_mass
                    PeakEnd[img_no] = upper_mass
                    PeakCenter[img_no] = Center_mass
        
                    bif6_image = bif6.Read_Image(  bif6_file, img_X_size, img_Y_size)
                    if trace:
                        print( 'img_no ', img_no, ' in range(0, ',num_of_images, ')', ' bif6_image.shape ', bif6_image.shape, type(bif6_image[0,0]))
                    if bif6_image.shape !=  (img_X_size, img_Y_size):
                        break
                        print('The BIF6 file appears to be truncated. Garbage data at mass '+str(PeakID_numeric[img_no, 0])+ ' and higher', 'Error')
                    else:
                        if trace:
                            print('bif6_image min, max', np.min(bif6_image), np.max(bif6_image))
#                        IonImages[ :, :, img_no ] = bif6_image
                        IonImages_full_array[ :, :, img_no ] = bif6_image
                
                self.enter_Data(Sample_name, 'IMAGE', IonImages_full_array)
                if trace:
                    print('SOURCE_FILE')
                self.enter_IDs(Sample_name, 'SOURCE_FILE', [source_filename])
                if trace:
                    print('META_INFO')
                self.enter_Data(Sample_name, 'CLASS_NUMBER', ClassNumber*np.ones((1,1)))
                if trace:
                    print('CLASS_NUMBER', ClassNumber*np.ones((1,1)))
                self.enter_IDs(Sample_name,'META_INFO', [os.path.basename(sys.argv[0])] )
                if trace:
                    print('VARID1')
                self.enter_IDs(Sample_name, 'VARID1', Get_TextBased_VariableIDs(PeakID_numeric, 'MS') )
                if trace:
                    print('VARID2')
                self.enter_Data(Sample_name, 'VARID2', PeakID_numeric)
                if trace:
                    print('VARID3')
                self.enter_Data(Sample_name, 'VARID3', IONTOF_Image_Index)
                if trace:
                    print('VARID4')
                self.enter_Data(Sample_name, 'VARID4', PeakBegin)
                if trace:
                    print('VARID5')
                self.enter_Data(Sample_name, 'VARID5', PeakEnd)
                if trace:
                    print('VARID6')
                self.enter_Data(Sample_name, 'VARID6', PeakCenter)
            return Sample_name

        

                

    def Mk_Matlab7_3_text_matrix(self, id_list ):
        # Put text from list into 16-bit integer matrix for matlab compatible text matrices in hdf5 style matlab 7.3 format
        maxlen = max( map( len, id_list))
        OutList = []
        for ID in id_list:
            ID_mapped = list(map( ord, ID.ljust( maxlen)))
            OutList.append(ID_mapped)
        TextMatrix = np.mat( OutList, dtype=np.uint16 ).T #Included the transpose here rather than in the main code
        return TextMatrix
        
    def Rd_Matlab7_3_text_matrix(self, TextMatrix ):
        id_list = []
        # print('Rd_Matlab7_3_text_matrix',TextMatrix.shape)
        # print(TextMatrix)
        for row in range(0, TextMatrix.shape[0]):
            if TextMatrix.shape[1] == 1:
                id_list.append( chr(TextMatrix[row,0]) )
            else:
                LettersID = map( chr, np.squeeze(np.asarray(TextMatrix[row]))  )
                id_list.append( ''.join(LettersID).strip() )
        return id_list
        
                
    def get_UnfoldedData(self, DataSetName, KeyName, bin_size_power=0, matlab_compatible=False): # 3D data set needed
        trace = False
        if bin_size_power == 0:
            ypixels = self.cache_file_handle[DataSetName][KeyName].shape[0]
            xpixels = self.cache_file_handle[DataSetName][KeyName].shape[1]

            if self.cache_file_handle[DataSetName][KeyName].ndim == 3:
                z_spectrum_len = self.cache_file_handle[DataSetName][KeyName].shape[2]                
                for_type_test = self.cache_file_handle[DataSetName][KeyName][0,0,0]
            elif self.cache_file_handle[DataSetName][KeyName].ndim == 2:
                z_spectrum_len = 1
                for_type_test = self.cache_file_handle[DataSetName][KeyName][0,0]
            if trace:
                print('for_type_test', type(for_type_test))
                print( self.cache_file_handle[DataSetName][KeyName].shape)
                
            if not isinstance(for_type_test, np.float64) and matlab_compatible:
                DataSet_in_float64 = self.cache_file_handle[DataSetName][KeyName][:].astype(np.float64)
                UnfoldedSpectra = np.reshape( DataSet_in_float64, (-1, z_spectrum_len))
            else:     
                UnfoldedSpectra = np.reshape( self.cache_file_handle[DataSetName][KeyName], (-1, z_spectrum_len))
                

        else:
            if self.cache_file_handle[DataSetName][KeyName].ndim != 3:
                print("Known limitation: ")
                print("    if there is only one variable (mass or wl) the present code does not allow for binning")
                UnfoldedSpectra = np.empty([])
                ypixels = self.cache_file_handle[DataSetName][KeyName].shape[0]
                xpixels = self.cache_file_handle[DataSetName][KeyName].shape[1]
            else:            
                HySp_img = self.get_binned3Dcube(DataSetName, KeyName, bin_size_power)
                ypixels = HySp_img.shape[0]
                xpixels = HySp_img.shape[1]
                if HySp_img.ndim == 3:
                    z_spectrum_len = HySp_img.shape[2]
                elif HySp_img.ndim == 2:
                    z_spectrum_len = 1
                UnfoldedSpectra = np.reshape( HySp_img, (-1, z_spectrum_len))

        YY, XX = np.mgrid[0:ypixels, 0:xpixels]  
        if matlab_compatible:
            img_index = np.mat(np.zeros( (ypixels*xpixels, 1), dtype=np.float64 )) # "zeros" - shortcut for one 3D image, needs increment for more images
            y_index = np.reshape(YY.astype(np.float64), (-1,1))
            x_index = np.reshape(XX.astype(np.float64), (-1,1))
        else:
            img_index = np.mat(np.zeros( (ypixels*xpixels, 1), dtype=np.int32 ))     
            y_index = np.reshape(YY, (-1,1))
            x_index = np.reshape(XX, (-1,1))
        
            
        if trace:
            print()
            print('UnfoldedSpectra.shape', UnfoldedSpectra.shape, type(UnfoldedSpectra[0,0]))
            print('img_index.shape', img_index.shape, type(img_index[0]))
            print('y_index.shape', y_index.shape, type(y_index[0]))
            print('x_index.shape', x_index.shape, type(x_index[0]))
            
        return UnfoldedSpectra, img_index, y_index, x_index
    
    
    def getUnfolded_IncludedPixels(self, DataSetName, KeyName, Included_pixels, bin_size_power=0, matlab_compatible=False):
        
        """ Returns an indexed unfolded array of selected observations from the 3D hyperspectral input
        
        getUnfolded_IncludedPixels(DataSetName, KeyName, Included_pixels)
        
        DataSetName:     The name of the loaded data set
        KeyName:         The name of the hyperspectral record where the selection takes place, 
                         should be a 3D array such as 'IMAGE'  
        Included_pixels: Assumed to be a boolean type folded 2D array in the same shape as the target image 
        
        output:          UnfoldedSpectra_sel_pix, img_index_sel_pix, y_index_sel_pix, x_index_sel_pix        
        """
#        ( spectra, obsid1, obsid2, obsid3, secondary_varid01_list, secondary_varid02, 
#          sec_varid03, sec_varid04, sec_varid05, pre_process_vector, meta_info, obsid1_names ) = Simca_P_matrices
#        bin_size_power = 0 #Same size as original image
        spectra, obsid1, obsid2, obsid3 = self.get_UnfoldedData(DataSetName, KeyName, bin_size_power, matlab_compatible)
        Included_pix_unfolded = np.reshape(Included_pixels, (-1,1))
        Incl_indices = getNpIndices( Included_pix_unfolded )
        UnfoldedSpectra_sel_pix = spectra[Incl_indices,:]
        img_index_sel_pix = obsid1[Incl_indices,:]
        y_index_sel_pix = obsid2[Incl_indices,:]
        x_index_sel_pix = obsid3[Incl_indices,:]
#        meta_info_non_backgr = []
#        meta_info_non_backgr.extend(meta_info)
#        meta_info_non_backgr.append('included_pixels=non_background')
        
#        Simca_P_matrices = ( spectra_non_backgr, obsid1_non_backgr, obsid2_non_backgr, obsid3_non_backgr, 
#                             secondary_varid01_list, secondary_varid02, sec_varid03, sec_varid04, sec_varid05, 
#                             pre_process_vector, meta_info_non_backgr, obsid1_names )                             
        return UnfoldedSpectra_sel_pix, img_index_sel_pix, y_index_sel_pix, x_index_sel_pix 
        
    
    def convert_UnfoldedData_to_HySpImage(self, y_index, x_index, UnfoldedSpectra, orig_HyImg_dims=[], repr_of_missing=0.0 ):
        traceFolding = False
        trace = False
        y_max = int(1+np.max(y_index))
        x_max = int(1+np.max(x_index))
        """Data in UnfoldedSpectra is transposed, ie spectra in columns"""
        if trace:
            print('y_max, x_max', y_max, x_max)
            print("UnfoldedSpectra.shape", UnfoldedSpectra.shape)
            
        if y_max*x_max == UnfoldedSpectra.shape[0]: # No pixels are missing
            if traceFolding:
                print('Folding alt.1')
#            data = UnfoldedSpectra.T
            image = np.reshape(UnfoldedSpectra, (y_max, x_max, UnfoldedSpectra.shape[1]))
            included_pixels = np.ones((y_max, x_max), dtype=np.bool)
            
        # Handle unfolded data with missing values
        elif orig_HyImg_dims:
            if traceFolding:
                print('Folding alt. 2')                        
            xpixels, ypixels, spectrum_len = orig_HyImg_dims
            image = np.ones((ypixels, xpixels, spectrum_len))*repr_of_missing
            included_pixels = np.zeros((ypixels, xpixels), dtype=np.bool)
            y_i = np.squeeze(np.asarray(np.round(y_index), dtype=np.int))
            x_i = np.squeeze(np.asarray(np.round(x_index), dtype=np.int))
#            data = UnfoldedSpectra.T
            for spc in range(UnfoldedSpectra.shape[0]):
                image[y_i[spc], x_i[spc], :] = UnfoldedSpectra[spc, :]
                included_pixels[y_i[spc], x_i[spc]] = True
        
        else: # when the original folded size is not known
            if traceFolding:
                print('Folding alt. 3')
            image = np.zeros((y_max, x_max, UnfoldedSpectra.shape[1]))
            included_pixels = np.zeros((y_max, x_max), dtype=np.bool)
            y_i = np.squeeze(np.asarray(np.round(y_index), dtype=np.int))
            x_i = np.squeeze(np.asarray(np.round(x_index), dtype=np.int))
#            data = UnfoldedSpectra.T
            for spc in range(UnfoldedSpectra.shape[0]):
                image[y_i[spc], x_i[spc], :] = UnfoldedSpectra[spc, :]
                included_pixels[y_i[spc], x_i[spc]] = True
        
        return image, included_pixels 



    def Save_unfolded_spectra_from_one_image(self, DataSetName, location_of_output_files, bin_size_power=0, matlab_compatible=False):

        UnfoldedSpectra, img_index, y_index, x_index = self.get_UnfoldedData(DataSetName, 'IMAGE', bin_size_power, matlab_compatible)
        if UnfoldedSpectra.ndim > 0:
            if bin_size_power == 0:
                OutputFileName = os.path.join(location_of_output_files, DataSetName + '-v73.mat')
            else:
                OutputFileName = os.path.join(location_of_output_files, DataSetName +'_binp'+str(bin_size_power)+ '-v73.mat')
            
            outfile = MatDataIO.Matlab7_3_file(OutputFileName)
            outfile.WriteMatrix('DATA', UnfoldedSpectra)
            outfile.WriteMatrix('OBSID1', img_index)
            outfile.WriteMatrix('OBSID2', y_index)
            outfile.WriteMatrix('OBSID3', x_index)
            RecordList = self.get_RecordNames(DataSetName)
            if 'CLASS_NUMBER' in RecordList:
                ClassNum = self.get_Data(DataSetName, 'CLASS_NUMBER')
                outfile.WriteMatrix('OBSID4', np.ones_like(img_index)*ClassNum)
            
            
            for key in sorted(self.cache_file_handle[DataSetName].keys()):
                if key not in ['IMAGE'] and (key[0:5] != 'OBSID'):
    #                    print( key )            
                    if 'MATLAB_class' in self.cache_file_handle[DataSetName][key].attrs:
    #                        print('   ',"'MATLAB_class' =", self.cache_file_handle[DataSetName][key].attrs[ 'MATLAB_class' ])
                        if self.cache_file_handle[DataSetName][key].attrs[ 'MATLAB_class' ] == 'char':
                            outfile.WriteIds( key, self.get_IDs(DataSetName, key))
                        else:
                            outfile.WriteMatrix( key, self.get_Data(DataSetName, key)[:] )
                    else:
                        print("'MATLAB_class' attribute was missing for", key)
            outfile.close()                      


    def Save_all_unfolded_spectra(self, location_of_output_files, bin_size_power=0, matlab_compatible=False):

        all_entries = list(self.cache_file_handle)
#        print('all_entries', all_entries)
        for DataSetName in all_entries:
            UnfoldedSpectra, img_index, y_index, x_index = self.get_UnfoldedData(DataSetName, 'IMAGE', bin_size_power, matlab_compatible)
            if bin_size_power == 0:
                OutputFileName = os.path.join(location_of_output_files, DataSetName + '-v73.mat')
            else:
                OutputFileName = os.path.join(location_of_output_files, DataSetName +'_binp'+str(bin_size_power)+ '-v73.mat')
            
            outfile = MatDataIO.Matlab7_3_file(OutputFileName)
            outfile.WriteMatrix('DATA', UnfoldedSpectra)
            outfile.WriteMatrix('OBSID1', img_index)
            outfile.WriteMatrix('OBSID2', y_index)
            outfile.WriteMatrix('OBSID3', x_index)
            RecordList = self.get_RecordNames(DataSetName)
            if 'CLASS_NUMBER' in RecordList:
                ClassNum = self.get_Data(DataSetName, 'CLASS_NUMBER')
                outfile.WriteMatrix('OBSID4', np.ones_like(img_index)*ClassNum)
            
            
            for key in sorted(self.cache_file_handle[DataSetName].keys()):
                if key not in ['IMAGE'] and (key[0:5] != 'OBSID'):
#                    print( key )            
                    if 'MATLAB_class' in self.cache_file_handle[DataSetName][key].attrs:
#                        print('   ',"'MATLAB_class' =", self.cache_file_handle[DataSetName][key].attrs[ 'MATLAB_class' ])
                        if self.cache_file_handle[DataSetName][key].attrs[ 'MATLAB_class' ] == 'char':
                            outfile.WriteIds( key, self.get_IDs(DataSetName, key))
                        else:
                            outfile.WriteMatrix( key, self.get_Data(DataSetName, key)[:] )
                    else:
                        print("'MATLAB_class' attribute was missing for", key)
            outfile.close()
            


    def Save_selected_unfolded_from_one_image(self, DataSetName, SelectedPixels, FileName, matlab_compatible=False):
        UnfoldedSpectra, img_index, y_index, x_index  = self.getUnfolded_IncludedPixels(DataSetName, 'IMAGE', SelectedPixels, matlab_compatible)
        OutputFileName = FileName + '-v73.mat'
        outfile = MatDataIO.Matlab7_3_file(OutputFileName)
        outfile.WriteMatrix('DATA', UnfoldedSpectra)
        outfile.WriteMatrix('OBSID1', img_index)
        outfile.WriteMatrix('OBSID2', y_index)
        outfile.WriteMatrix('OBSID3', x_index)
        for key in sorted(self.cache_file_handle[DataSetName].keys()):
            if key not in ['IMAGE']:
#                    print( key )            
                if 'MATLAB_class' in self.cache_file_handle[DataSetName][key].attrs:
#                        print('   ',"'MATLAB_class' =", self.cache_file_handle[DataSetName][key].attrs[ 'MATLAB_class' ])
                    if self.cache_file_handle[DataSetName][key].attrs[ 'MATLAB_class' ] == 'char':
                        outfile.WriteIds( key, self.get_IDs(DataSetName, key))
                    else:
                        outfile.WriteMatrix( key, self.get_Data(DataSetName, key)[:] )
                else:
                    print("'MATLAB_class' attribute was missing for", key)
        outfile.close()
        


    def Read_FoldingImutable_mat73_entries(self, hdf5_obj, DataSetName):
        trace = False
        for key in sorted(hdf5_obj.keys()):
            if key not in ['IMAGE', 'DATA'] and (key[0:5] != 'OBSID'):
                if trace:
                    print( 'hdf5_obj key=', key, ' matlab_class:', hdf5_obj[key].attrs['MATLAB_class'])
                    print( key, type(hdf5_obj[key][:] ))            
                if 'MATLAB_class' in hdf5_obj[key].attrs:
#                        print('   ',"'MATLAB_class' =", self.cache_file_handle[DataSetName][key].attrs[ 'MATLAB_class' ])
                    if (hdf5_obj[key].attrs[ 'MATLAB_class' ] == 'char') or \
                       (hdf5_obj[key].attrs[ 'MATLAB_class' ] == b'char'):
                        mat_chars = hdf5_obj[key][:].T
                        mat_list = self.Rd_Matlab7_3_text_matrix(mat_chars)
                        self.enter_IDs( DataSetName, key, mat_list )
                    elif (hdf5_obj[key].attrs[ 'MATLAB_class' ] == 'logical') or \
                       (hdf5_obj[key].attrs[ 'MATLAB_class' ] == b'logical'):
                        self.enter_Logical(DataSetName, key, hdf5_obj[key])   
                    else:
                        self.enter_Data(DataSetName, key, hdf5_obj[key])
                else:
                    print("'MATLAB_class' attribute was missing for", key)


    def Read_one_file_with_unfolded_spectra(self, FileName):
        """ Read an unfolded hyperspectral image as written by this module """
        trace = False
        DataSetName = None
        if trace:
            print('Read_one_file_with_unfolded_spectra')
        if not os.path.isfile(FileName):
            print()
            print('The following filename does not exist, check if special characters have different coding:')
            print(FileName)
        else:
            DataSetName = os.path.basename(os.path.splitext(FileName)[0]).split('-v73')[0]
            hdf5_obj = h5py.File( FileName, 'r' )
            try:
                if not set(['DATA', 'OBSID2', 'OBSID3']).issubset(hdf5_obj.keys()):
                    print("The file", DataSetName , "does not contain the entries 'DATA', 'OBSID2', 'OBSID3'")
                    DataSetName = None
                else:
                    if 'FOLDED_SIZE' in hdf5_obj.keys():
                        image, included_pixels = self.convert_UnfoldedData_to_HySpImage(hdf5_obj['OBSID2'][:], 
                                                                                        hdf5_obj['OBSID3'][:], 
                                                                                        hdf5_obj['DATA'][:].T, 
                                                                                        hdf5_obj['FOLDED_SIZE'][:] )
                    else:
                        image, included_pixels = self.convert_UnfoldedData_to_HySpImage(hdf5_obj['OBSID2'][:], 
                                                                                        hdf5_obj['OBSID3'][:], 
                                                                                        hdf5_obj['DATA'][:].T )                                       
                    if trace:
                        print('image', image.shape)
                                            
                    self.enter_Data(DataSetName, 'IMAGE', image)
                    self.Read_FoldingImutable_mat73_entries(hdf5_obj, DataSetName)
                    self.update_Logical(DataSetName, 'NON_MISSING_PIX', included_pixels)
                    self.update_IDs(DataSetName, 'LAST_FILE', FileName)
                    if not 'SOURCE_FILE' in self.get_RecordNames(DataSetName):
                        self.enter_IDs(DataSetName, 'SOURCE_FILE', FileName)
                        
            finally:
                hdf5_obj.close()
                if trace:
                    print('hdf5_obj was closed')
            
        return DataSetName
    

    def Add_cluster_colors(self, DataSetName, max_num_of_clusters=4 ):
        """ Use k-means to find clusters starting at 2 ending at max number of clusters
            Put the labels as a separate integer 3D array matching the original image 
            with one layer for each number of clusters"""
        trace = True
        KeyName = 'IMAGE'
        ypixels = self.cache_file_handle[DataSetName][KeyName].shape[0]
        xpixels = self.cache_file_handle[DataSetName][KeyName].shape[1]
        z_spectrum_len = self.cache_file_handle[DataSetName][KeyName].shape[2]             
        UnfoldedSpectra = np.reshape( self.cache_file_handle[DataSetName][KeyName], (-1, z_spectrum_len))        
        FoldedLabels = np.zeros((ypixels, xpixels, max_num_of_clusters-1), dtype=np.int32)
        
        for i in range(0, max_num_of_clusters-1):
            clusters = i+2
            print('clusters', clusters)
            kmeans = KMeans(init='k-means++', n_clusters=clusters, n_init=10)
            kmeans.fit(UnfoldedSpectra)
            labels = np.mat(kmeans.labels_).T
            if trace:
                print('label info',labels.shape, type(labels), type(labels[0,0]) )
                print('(ypixels, xpixels, labels.shape)', (ypixels, xpixels, labels.shape))
            # Refold needed for color labels
            FoldedLabels[:,:,i] = np.reshape(labels, (ypixels, xpixels, 1))
            
        self.enter_Data(DataSetName, 'ClusterColors', FoldedLabels )

        
    def Split_image(self, Dset, split_exponent, ClassNumber=1, suffix='A'):
        trace = False
        
        num_splits = 2 ** int(split_exponent) # number of splits per dimension
        if trace:
            print('num_splits',num_splits ,type(num_splits))
        
        New_sample_names = []
        hysp_image0 = np.asarray(self.get_binned3Dcube(Dset,'IMAGE'))
        source_file = self.get_SourceFilePath(Dset)
        RecordNames = self.get_RecordNames(Dset)
        print('RecordNames', RecordNames)
        VARIDs = []
        for key in RecordNames:
            if key[0:5] == 'VARID':
                VARIDs.append(key)
                if trace:
                    print(key, 'is_text:', self.is_text(Dset, key))
        
        one_splitted_hysp_image = np.zeros((hysp_image0.shape[0] // num_splits, hysp_image0.shape[1] // num_splits, hysp_image0.shape[2]))
    
        
        y_step = hysp_image0.shape[0] // num_splits
        x_step = hysp_image0.shape[1] // num_splits
        z_fill_amount = int(np.ceil(np.log10(num_splits*num_splits)))
        split_ix = 0
        for y_ix in range(num_splits):
            for x_ix in range(num_splits):
                if trace:
                    print('y_ix, x_ix, split_img', y_ix, x_ix, split_ix)
    
                one_splitted_hysp_image = hysp_image0[y_ix*y_step:(y_ix+1)*y_step, x_ix*x_step:(x_ix+1)*x_step, :]
            
                Sample_name = Dset+'_'+suffix + str(split_ix+1).zfill(z_fill_amount)
                if trace:
                    print('Processing dataset:', Sample_name)
                sys.stdout.flush()
                self.enter_Data(Sample_name, 'IMAGE', one_splitted_hysp_image)
                New_sample_names.append(Sample_name)
                self.enter_IDs(Sample_name, 'SOURCE_FILE', source_file)
                self.enter_Data(Sample_name, 'CLASS_NUMBER', ClassNumber*np.ones((1,1)))
                self.enter_IDs(Sample_name,'META_INFO', os.path.basename(sys.argv[0]) )
                for varid in VARIDs:
                    if self.is_text(Dset, varid):
                        self.enter_IDs(Sample_name, varid, self.get_IDs(Dset, varid))
                    else:
                        self.enter_Data(Sample_name, varid, self.get_Data(Dset, varid))
                split_ix += 1
    
        split_hysp_image_AllPixels = np.ones((hysp_image0.shape[0] // num_splits, hysp_image0.shape[1] // num_splits), dtype=np.bool)
        return New_sample_names, split_hysp_image_AllPixels

        
            
        
if __name__ == '__main__':
    tmp_cache_file = 'Test01_hysp_cache41.hdf5'
    
    if os.path.isfile(tmp_cache_file):
        os.remove(tmp_cache_file)
    hysp_cache = HyperSpectralCache(tmp_cache_file)
    
#    zipped_fname = '/home/mats_j/Data/DatO 2013/2013-09-26 Jonas Pulveregenskaper/BIF6/BDP+Leucine+Lactose/Till nya modeller/BDP+Leucine+Lactose p1 positive delay 50x50 256pix 130417_1.BIF6.zip'    
#    hysp_cache.load_ZippedBIF6_files(zipped_fname)
    
#    fname = '/home/mats_j/Data/DatO 2013/2013-09-26 Jonas Pulveregenskaper/BIF6/BDP+Leucine+Lactose/Till nya modeller/BDP+Leucine+Lactose p1 positive delay 50x50 256pix 130417_1.BIF6'
#    hysp_cache.load_BIF6_file(fname)

#    hysp_cache.enter_Data('DataSet01', 'DATA', get_data3() )
#    hysp_cache.enter_Data('DataSet01', 'OBSID1', get_data3()[:,0,0] )
#    hysp_cache.create_EmptyArray( 'DataSet01', 'IMAGE', (100,100,3) )
#    
#    print(hysp_cache.get_ListOfDataSets())
#    
#    a = hysp_cache.get_Data('DataSet01', 'DATA')
#    print(a)
#    print(a.parent)
#    print(a.name, a.shape, a.dtype)
#    print()
#    print(a[:])
#    print()
#    b = hysp_cache.get_binned_3Dslice('BDP+Leucine+Lactose p1 positive delay 50x50 256pix 130417_1', 'IMAGE', 8)
#    print('b', b.shape)
#    print(b)

    FileName = 'DbgOutFiles/2bdp_delex_pos_particle1_2-v73.mat'
    hysp_cache.Read_one_file_with_unfolded_spectra(FileName)
    print('File loaded')
    print()
    DataSetList = hysp_cache.get_ListOfDataSets()    
    print('DataSetList',DataSetList)
    RecordNames = hysp_cache.get_RecordNames(DataSetList[0])
    print('RecordNames', RecordNames)
    
    hysp_cache.close()
    
    print('Finished')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

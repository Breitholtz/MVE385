import os
import numpy as np
import numpy.linalg as linalg
import scipy
import ReadBIF6 as bif6
import hyperspectral_cache as hsc
import MVA_Lib as mva

def main():

    tmp_cache_fileneg = 'Negative_cache.hdf5'
    tmp_cache_filepos = 'Positive_cache.hdf5'

    if os.path.isfile(tmp_cache_fileneg):
        os.remove(tmp_cache_fileneg)
    if os.path.isfile(tmp_cache_fileneg):
        os.remove(tmp_cache_filenpos)
    hysp_cache_neg = hsc.HyperSpectralCache(tmp_cache_fileneg)
    #hysp_cache_pos = hsc.HyperSpectralCache(tmp_cache_filepos)

    FileNameNeg = '88Lac10BUD2MgStChalmersBi1HiMassn1_1-v73.mat'
    FileNamePos = '88Lac10BUD2MgStChalmersBi1HiMassp1_1-v73.mat'
    hysp_cache_neg.Read_one_file_with_unfolded_spectra(FileNameNeg)
    #hysp_cache_pos.Read_one_file_with_unfolded_spectra(FileNamePos)
    print('File loaded')
    DataSetList = hysp_cache_neg.get_ListOfDataSets()
    print('DataSetList',DataSetList)
    RecordNames = hysp_cache_neg.get_RecordNames(DataSetList[0])
    print('RecordNames', RecordNames)
    Tmpstr = '/' + DataSetList[0]
    print(Tmpstr)
    print('Image',hysp_cache_neg.cache_file_handle[Tmpstr]['IMAGE'])

    binning=0
    DsetList = hysp_cache_neg.get_ListOfDataSets()
    X0, img_index, y_index, x_index = hysp_cache_neg.get_UnfoldedData(DsetList[0], 'IMAGE', binning)

    center,centrum = mva.center(X0)
    print(X0.shape)
    for i in range(1,100):
    T, P, S = mva.PCA_by_randomizedSVD(X0, 4)
    #print(center)
    #print(centrum)

if __name__ == '__main__':
    main()

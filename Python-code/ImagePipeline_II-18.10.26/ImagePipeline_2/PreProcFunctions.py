#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 17 23:41:57 2017

@author: mats_j
"""

import numpy as np


def log1divT(spc, src_var_ix, tgt_var_ix):
    absorbance = -np.log10(spc)
    additional_vars = np.empty((0))
    return absorbance, additional_vars

def Subt_mean(data, src_var_ix, tgt_var_ix): # Part 1 of SNV
    mean_values = np.mean(data[:,src_var_ix], axis=1, keepdims=True) 
    """ Orientation of the mean vector is kept for easier hstack-ing later by 
        keeping it as a 2 dimensional array using keepdims"""
    one_row = np.mat(np.ones_like(data[0,tgt_var_ix]))

    """subt_data needs to have the same shape as the input data otherwise indexing 
       will be wrong in subsequent processing steps, testing to fill it with NaNs """
    subt_data = np.ones_like(data)*np.NaN
    subt_data[:,tgt_var_ix] = np.asarray(data[:,tgt_var_ix] - mean_values*one_row)
#    subt_data = np.hstack((subt_data, mean_values))
    print('subt_data',subt_data.shape)
    print('mean_values', mean_values.shape)
    return subt_data, mean_values
    
def Norm_by_Sdev(data, src_var_ix=np.empty([]), tgt_var_ix=np.empty([])): # Part 2 of SNV
    if src_var_ix.shape:
        Sdev = np.std(data[:,src_var_ix], axis=1, ddof=1, keepdims=True)
    else:
        Sdev = np.std(data, axis=1, ddof=1, keepdims=True)
    if tgt_var_ix.shape:
        columns = np.ones_like((data[0,tgt_var_ix]))
        scalers = np.outer(1/Sdev, columns )
        norm_data = np.ones_like(data)*np.NaN
        norm_data[:,tgt_var_ix] = np.multiply(data[:,tgt_var_ix], scalers)
    else:
        columns = np.ones_like((data[0,:]))
        scalers = np.outer(1/Sdev, columns )
#        norm_data = np.ones_like(data)*np.NaN
        norm_data = np.multiply(data, scalers)
    print('scalers',scalers.shape)
    print('norm_data',norm_data.shape)
    print('Sdev', Sdev.shape)
    return norm_data, Sdev

def SNV(spectra):
    mean_spectrum = np.mean(spectra, axis=1)
    SNV_spectra = np.std(np.subtract(spectra, mean_spectrum, ddof=1))
    return SNV_spectra


def Poisson_weights( Current_X_average, is_offset_correction ):
    """
    Calculate Poisson weights from Model average in 2D-array or np.mat matrix
    for all positive values in X_average, if negative or zero, zero weights are set
    Alternatively, add a 3% offset J.Chemo. 2008, 22, 500-509 
    Output: Poisson_weights in 2D-array
    """

    Model_X_avg = np.array(Current_X_average)
    if is_offset_correction:
        offset_corr = 0.03 * np.max(Model_X_avg)
        # print( 'offset_corr ', offset_corr
        Model_X_avg_offset = Model_X_avg + offset_corr
        Poisson_weights_out = np.power(Model_X_avg_offset, -0.5 )
    else: # No offset, correct only for presence of zeros    
        positive_pos = (Model_X_avg > 0)
        Poisson_weights_out = np.zeros((1,Model_X_avg.shape[1]))
        Poisson_weights_out[positive_pos] = np.power(Model_X_avg[positive_pos], -0.5 )
    return Poisson_weights_out


def Poisson_scaling(mass_spectra, spectral_average_of_image, is_offset_correction=True):
        
    poiss_w = Poisson_weights( spectral_average_of_image, is_offset_correction )
    Poiss_scaled_spectra = np.multiply( mass_spectra, poiss_w )
    return Poiss_scaled_spectra
    
    
    
    
    
    
    
    
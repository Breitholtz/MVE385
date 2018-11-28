import numpy as np

import pywt
import pywt.data

def wavelet_image_fusion(hyper_image_1, hyper_image_2, region_to_fuse,depth_of_wavelet):
 #Image 1 and 2 must have be 3-dimensional arrays with sizes n*m*k
 #region_to_fuse is a n*m boolean array telling which regions to fuse in the images
 #depth_of_wavelet, the nbr of levels in the multilevel 2D wavelet transform
 tmp1,tmp2,nbr_spectrs = size(hyper_image_1)
  # Fuse each spectrum layer
  for i in (0,nbr_spectrs):
   # perform (multilevel) 2D wavelet transform
   # To do: implement multilevel wavelet and handle arbitrary outputs
   #
   approx_coeffs_1, (horizontial_coeffs_1, vertixal_coeffs_1, diagonal_coeffs_1) = pywt.wavedec2(hyper_image_1, haar, level=1)
   approx_coeffs_2, (horizontial_coeffs_2, vertixal_coeffs_2, diagonal_coeffs_2) = pywt.wavedec2(hyper_image_2, haar, level=1)
   
   for j in (0,depth_of_wavelet):
    
   
  
  

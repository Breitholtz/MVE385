import numpy as np

import pywt
import pywt.data

def wavelet_image_fusion(hyper_image_1, hyper_image_2, region_to_fuse,depth_of_wavelet):
    #Image 1 and 2 must be 3-dimensional arrays with the same size,  n*m*k
    #region_to_fuse is a n*m boolean array telling which regions to fuse in the images
    #depth_of_wavelet, the nbr of levels in the multilevel 2D wavelet transform
    (height,width,nbr_spectrs) = hyper_image_1.shape
    # initialize the fused images
    fused_image = np.zeros(height, width, nbr_spectrs)
    fused
    # Fuse each spectrum layer
    for spect in (0,nbr_spectrs):
        # perform (multilevel) 2D wavelet transform
        # To do: implement multilevel wavelet and handle arbitrary outputs
        # coeffs_i = [cAn, (cHn, cVn, cDn), … (cH1, cV1, cD1)], n = depth_of_wavelet
        coeffs_1 = pywt.wavedec2(hyper_image_1[:,:,spect], haar, level=depth_of_wavelet)
        coeffs_2 = pywt.wavedec2(hyper_image_2[:,:,spect], haar, level=depth_of_wavelet)
        fused_coeffs = []
        # Fuse each level
        for l in (length(coeffs_1),0,-2):
            cAl_1 = coeffs_1[l]
            (cHl_1, cVl_1, cDl_1) = coeffs_1[l + 1]
            cAl_2 = coeffs_2[l]
            (cHl_2, cVl_2, cDl_2) = coeffs_2[l + 1]
            (height_transf,width_transf) = cAl_1.shape
            fused_cAl, fused_cHl, fused_cVl, fused_cDl = np.zeros([height_transf,width_transf])
            # Average/maximum fusion rules
            for i in (0,height_transf):
                for j in (0,width_transf):
                    fused_cAl = (cAl_1[i,j] + cAl_2[i,j])/2
                    fused_cHl = np.maximum(cHl_1, cHl_2)
                    fused_cVl = np.maximum(cVl_1, cVl_2)
                    fused_cDl = np.maximum(cDl_1, cDl_2)

            fused_coeffs.append(fused_cAl)
            fused_coeffs.append((fused_cHl, fused_cVl, fused_cDl))
        fused_image[,,spect] = pywt.waverec2(fused_coeffs, haar, level=depth_of_wavelet)
    return(fused_image)

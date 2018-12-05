import os, sys
import ReadBIF6 as read
import hyperspectral_cache as cache
import numpy as np

def image_contrast(image):
    N=image.shape[0]
    M=image.shape[1]
    Ibar=image.mean()
    Sum=0
    for i in range(0,N):
        for j in range(0,M):
            Sum+=np.power(image[i][j]/Ibar-1,2)
    Sum=Sum/(N*M)
    Result=np.sqrt(Sum)
    print(Result)
    return Result

def image_quality(image):
    scale=100 # scale factor
    N=image.shape[0]
    M=image.shape[0]
    t_h=0 #
    F=np.fft.fft2(image)
    Fcenter=np.fft.fftshift(F)
           
    Max=(np.abs(Fcenter).max)
    for i in range(0,N):
        for j in range(0,M):
            if np.abs(Fcenter[i][j]>Max/scale):
                t_h+=1
    Result= t_h/(N*M)
    print(Result)
    return Result

def fuse_Spectra(spec_Neg,spec_Pos):
	spectra = []
	spectra.append(np.maximum(spec_Pos[0],spec_Neg[0])) #note remove first spectra for only overlapping spectras
	j=1
	i=1
	k=0
	while i < spec_Neg.size and j < spec_Pos.size:
		if spec_Pos[j]<= spectra[k]:
			j+=1
		elif spec_Neg[i]<=spectra[k]:
			i+=1
		else:
			spectra.append(np.maximum(spec_Pos[j],spec_Neg[i]))
			k=k+1;
	return spectra

def get_New_Spectra(spectra,fused_Spectra):
	k=1;
	i=1;
	new_Spectra = []
	map_i = [] #map index
	map_p = [] #map procent
	while i<spectra.size and k<fused_Spectra.size:
		if spectra[i] <= fused_Spectra[k]:
			map_i.append(k)
			if spectra[i-1]>=fused_Spectra[k-1]:
				map_p[i]=1
			else:
				map_p[i]=(spectra[i]-fused_Spectra[k-1])/(spectra[i]-spectra[i-1])
			i=i+1
		else:
			k=k+1
	return map_p

def main():

	infilen ="88Lac10BUD2MgStChalmersBi1HiMassn1_1.BIF6.zip" #spectra files
	infilep ="88Lac10BUD2MgStChalmersBi1HiMassp1_1.BIF6.zip"
	# create cache object
	if os.path.isfile("ImageCachen.hdf5"):
		os.remove("ImageCachen.hdf5") # remove if we had a previous cache object
	if os.path.isfile("ImageCachep.hdf5"):
		os.remove("ImageCachep.hdf5")

	hysp_cachen=cache.HyperSpectralCache("ImageCachen.hdf5")
	hysp_cachep=cache.HyperSpectralCache("ImageCachep.hdf5")

	# unzip file
	hysp_cachen.load_ZippedBIF6_files(infilen)
	hysp_cachep.load_ZippedBIF6_files(infilep)
	DataSetListn = hysp_cachen.get_ListOfDataSets()
	DataSetListp = hysp_cachep.get_ListOfDataSets()

	# open the loaded BIF6 file and read the data
	spectran, imgindexn, yn, xn = hysp_cachen.get_UnfoldedData(DataSetListn[0],'IMAGE')
	spectrap, imgindexp, yp, xp = hysp_cachep.get_UnfoldedData(DataSetListp[0],'IMAGE')

	Tmpstrn = '/' + DataSetListn[0]
	Tmpstrp = '/' + DataSetListp[0]
	VARID4n = hysp_cachen.cache_file_handle[Tmpstrn]['VARID4'] # get max spectra
	VARID4p = hysp_cachep.cache_file_handle[Tmpstrp]['VARID4']

	spectra=fuse_Spectra(VARID4n,VARID4p) #fuse spectras to an overlapping spectra
	#print(spectra)
	spectra_pos=get_New_Spectra(VARID4p,spectra)




if  __name__ =='__main__':
	main()

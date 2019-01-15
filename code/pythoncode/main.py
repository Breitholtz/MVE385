import os, sys
import ReadBIF6 as read
import hyperspectral_cache as cache
import numpy as np
import MVA_Lib as MVA

#image contrast by variance
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
    return Result

#image quality by fourier transform
def image_quality(image):
    scale=100 # scale factor
    N=image.shape[0]
    M=image.shape[1]
    t_h=0 # amount of high freq 'components'
    F=np.fft.fft2(image)
    Fcenter=np.fft.fftshift(F)
    MAX=np.max(np.absolute(Fcenter))

    for i in range(0,N):
        for j in range(0,M):
            if np.abs(Fcenter[i][j])>MAX/scale:
                t_h+=1
    Result= t_h/(N*M)
    return Result

#fuse negative and postive spectras to one spectra profile
def fuse_Spectra_Profile(spec_Neg,spec_Pos):
	spectra = []
	spectra.append(np.maximum(spec_Pos[0],spec_Neg[0]))
	j=1
	i=1
	k=0
	while i < spec_Neg.size-1 or j < spec_Pos.size-1:
		while spec_Pos[j] <= spectra[k] and j<spec_Pos.size-1:
			j+=1
		while spec_Neg[i]<=spectra[k] and i <spec_Neg.size-1:
			i+=1
		spectra.append(np.maximum(spec_Pos[j],spec_Neg[i]))
		k=k+1;
	return spectra

#get map from spectra to fused spectra
def get_map(spectra,fused_Spectra):
	k=0;
	i=1;
	new_Spectra = np.zeros(len(fused_Spectra))
	map_i = np.zeros(len(spectra),dtype=np.int) #map index
	map_p = np.zeros(len(spectra)) #map procent
	map_i[0]=0
	map_p[0]=1
	while i < spectra.size and k < len(fused_Spectra):
		if spectra[i] <= fused_Spectra[k]:
			map_i[i]=k
			if spectra[i-1]>=fused_Spectra[k-1]*min(k,1):#argument for initial spectrums
				map_p[i]=1
			else:
				map_p[i]=((spectra[i]-fused_Spectra[k-1])/(spectra[i]-spectra[i-1]))
			i=i+1
		else:
			k=k+1
	return map_p, map_i #return index and procentage mapped

#get new concentration in fused spectra
def get_New_Concentration(X,fused_Spectra,map_p,map_i):
	print('len(X)',len(X))
	print('len(fused_Spectra)',len(fused_Spectra))
	print('map_i.size',map_i.size)
	conc=np.zeros((len(X),len(fused_Spectra)))



	for j in range(map_i.size):
		k=map_i[j]
		pros=map_p[j]
		for i in range(len(X)):
			conc[i][k]=conc[i][k]+X[i][j]*pros
			if pros < 1:
				conc[i][k-1]=conc[i][k-1]+X[i][j]*(1-pros)
	return conc

def remove_Colomns(x_Mat,Max): #removes colomns not wanted

	return x_Mat[:,1:Max]

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
	Xn, imgindexn, yn, xn = hysp_cachen.get_UnfoldedData(DataSetListn[0],'IMAGE')
	Xp, imgindexp, yp, xp = hysp_cachep.get_UnfoldedData(DataSetListp[0],'IMAGE')

	Tmpstrn = '/' + DataSetListn[0]
	Tmpstrp = '/' + DataSetListp[0]
	VARID4n = hysp_cachen.cache_file_handle[Tmpstrn]['VARID4'] # get max spectra profile
	VARID4p = hysp_cachep.cache_file_handle[Tmpstrp]['VARID4']
	spectra_Profile=fuse_Spectra_Profile(VARID4n,VARID4p) #fuse spectras to an overlapping spectra profile

	spectra_p_Pos, spectra_i_Pos=get_map(VARID4p,spectra_Profile) # create new concentration by mapping from old spectra to fused spectra profile
	spectra_p_Neg, spectra_i_Neg=get_map(VARID4n,spectra_Profile)
	print(spectra_p_Neg, spectra_i_Neg)
	print(spectra_p_Pos, spectra_i_Pos)

	Xneg_Pre=get_New_Concentration(Xn,spectra_Profile,spectra_p_Neg,spectra_i_Neg)# new concentartion with fused spectra
	Xpos_Pre=get_New_Concentration(Xp,spectra_Profile,spectra_p_Pos,spectra_i_Pos)
	Xneg= remove_Colomns(Xneg_Pre,min((spectra_i_Neg[-1],spectra_i_Pos[-1])))#remove unwanted colomns
	Xpos= remove_Colomns(Xpos_Pre,min((spectra_i_Neg[-1],spectra_i_Pos[-1])))

	print('shape',Xneg.shape)
	print('shape',Xpos.shape)
	del Xp
	del Xn
	Xneg=Xneg*Xpos.mean()/Xneg.mean() # same average for positive and negative
	PCA_Mat=np.vstack((Xpos,Xneg)) # pre PCA matrix both stacked togheter vertically
	components=4
	T, P, S = MVA.PCA_by_randomizedSVD(PCA_Mat, components)#PCA
	print('T.shape',T.shape)

	PCA = np.vsplit(T, 2) #split matrix into pos/negative image
	PCA_Pos = PCA[0]
	PCA_Neg = PCA[1]

	print('PCA_pos.shape:',PCA_Pos.shape)
	print('PCA_neg.shape:',PCA_Neg.shape)

if  __name__ =='__main__':
	main()

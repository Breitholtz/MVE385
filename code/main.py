import os, sys
import ReadBIF6 as read
import hyperspectral_cache as cache
import numpy as np

#fuse negative and postive spectras to one spectra profile
def fuse_Spectra_Profile(spec_Neg,spec_Pos):
	spectra = []
	spectra.append(np.maximum(spec_Pos[0],spec_Neg[0]))
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

#get map from spectra to fused spectra
def get_map(spectra,fused_Spectra):
	k=1;
	i=1;
	new_Spectra = np.zeros(len(fused_Spectra))
	map_i = np.zeros(len(spectra)) #map index
	map_p = np.zeros(len(spectra)) #map procent
	map_i[0]=0
	map_p[0]=1
	while i < spectra.size and k < len(fused_Spectra):
		if spectra[i] <= fused_Spectra[k]:
			map_i[i]=k
			if spectra[i-1]>=fused_Spectra[k-1]:
				map_p[i]=1
			else:
				map_p[i]=((spectra[i]-fused_Spectra[k-1])/(spectra[i]-spectra[i-1]))
			i=i+1
		else:
			k=k+1
	return map_p, map_i #return index and procentage mapped

#get new concentration in fused spectra
def get_New_Concentration(X,fused_Spectra,map_i,map_p):
	con=np.zeros(X.size,len(fused_Spectra))

	for i in range[len(fused_Spectra)]:
		for j in range[X.size]:
			k=map_i[j]
			pros=map_p[j]
			conc[i][k]=conc[i][k]+x[i][j]*pros
			if pros < 1 and k>0:
				conc[i][k-1]=conc[i][k-1]+x[i][j]*(1-pros)

	return conc

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
	#print(spectra)
	spectra_p_Pos, spectra_i_Pos=get_map(VARID4p,spectra_Profile) # create new concentration by mapping from old spectra to fused spectra profile
	spectra_p_Neg, spectre_i_Neg=get_map(VARID4n,spectra_Profile)

	#
	Xneg=get_New_Concentration(Xn,spectra_Profile,spectra_p_Neg,spectre_i_Neg)
	Xpos=get_New_Concentration(Xp,spectra_Profile,spectra_p_Pos,spectre_i_Pos)
	print(Xneg)


if  __name__ =='__main__':
	main()

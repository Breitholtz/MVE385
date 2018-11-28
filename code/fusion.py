#
# This is the shell code for the image fusion program
# 
import os, sys
import ReadBIF6 as read
import cache
import numpy as np
# Read in Bif6-file


# PCA to find most relevant data to fuse


# (processing to deal with skewed images etc. if needed!)


# Take data and use chosen algorithm to fuse the images


# return final image with correlation data to the pre-fusion images
def get_data3():
	return np.arange(60).reshape([3, 4, 5]).copy()

def main(): #(image1,image2):

	indir="..\data\zipped_BIF6"
	infname ="88Lac10BUD2MgStChalmersBi1HiMassn1_1.BIF6.zip"
	infile=os.path.join(indir,infname)
	print(infile)

	# create cache object
	if os.path.isfile("ImageCache.hdf5"):
	  os.remove("ImageCache.hdf5") # remove if we had a previous cache object
	hysp_cache=cache.HyperSpectralCache("ImageCache.hdf5")

	# unzip file
	hysp_cache.load_ZippedBIF6_files(infile)
	DataSetList = hysp_cache.get_ListOfDataSets()
	print("DataSetList",DataSetList)

	# open the loaded BIF6 file and read the data
	spectra, imgindex, y, x = hysp_cache.get_UnfoldedData(DataSetList[0],'IMAGE')		

	print(spectra)
	print(spectra.shape)

	#f = open("88Lac10BUD2MgStChalmersBi1HiMassn1_1.BIF6",'rb')
	#hysp_cache.load_BIF6_file(filename)

		#num_images, img_x, img_y = read.Read_FileInfo(filename)
		# make arrays here?

		#Img_index, center_mass, lower_mass, upper_mass = read.Read_ImageInfo(filename)

		#bif6img = read.Read_Image(filename, img_x, img_y)


	



if  __name__ =='__main__':
	main()

import struct
import os, sys
import numpy as np

def Read_FileID( f ):
    Filetype_ID = f.read(6)
    data = struct.unpack('<hcccc', Filetype_ID )
#    print('Read_FileID',data)
    if data == (0, b'B', b'I', b'F', b'6'):
        return True
    else:
        return False
    
def Read_FileInfo( f ):
    FileInfo_hdr = f.read(6)
    FileInfo = struct.unpack('hhh', FileInfo_hdr )
    num_of_images, img_X_size, img_Y_size = FileInfo
    return num_of_images, img_X_size, img_Y_size

def Read_ImageInfo( f ):
    ImageInfo_hdr =  f.read(16)
    ImageInfo = struct.unpack('<lfff', ImageInfo_hdr )
    ImageIndex, Center_mass, lower_mass, upper_mass = ImageInfo
    return ImageIndex, Center_mass, lower_mass, upper_mass
   
def Read_Image( f, img_X_size, img_Y_size):
#    img1 = np.fromfile( f, dtype=np.uint32, count=img_X_size*img_Y_size )
    imc_rec_size = img_X_size*img_Y_size*4 # in bytes 
    img1 = np.fromstring( f.read(imc_rec_size), dtype=np.uint32 )
    Size_img1 = len( img1 )
    img1.shape = (Size_img1 // img_X_size, img_X_size )
    return img1
    
    
#def Get_TextBased_VariableIDs(X_scale0):
#    # The aim with this function is to round to 2 decimals to fit with TOF-SIMS data done earlier than 
#    # 2015-04-16 while rounding to 3 decimals when needed for new data
#    X_scale = np.squeeze(np.asarray(X_scale0))
#    # print 'X_scale.shape ', X_scale.shape
#    X_scale_IDs = []
#    min_diff2dec = np.min(np.diff(np.around(X_scale, decimals=2)))
#    min_diff3dec = np.min(np.diff(np.around(X_scale, decimals=3)))
#    min_diff4dec = np.min(np.diff(np.around(X_scale, decimals=4)))
#    # print 'min_diff_after_rounding to 2,3,4 decimals', min_diff2dec, min_diff3dec, min_diff4dec
#    if min_diff2dec > 0.01:
#        for scale_mark in range( 0, X_scale.shape[0] ):            
#            X_scale_IDs.append( 'mz_'+ '%.2f' % X_scale[scale_mark])                
#    elif min_diff3dec > 0.001:
#        for scale_mark in range( 0, X_scale.shape[0] ):
#            X_scale_IDs.append( 'mz_'+ '%.3f' % X_scale[scale_mark])
#    elif min_diff4dec >= 0.0001:
#        for scale_mark in range( 0, X_scale.shape[0] ):
#            X_scale_IDs.append( 'mz_'+ '%.4f' % X_scale[scale_mark])
#    else:
#        print( 'The X_scale entries are not unique, please redo the x_scale')
#        for scale_mark in range( 0, X_scale.shape[0] ):
#            scale_entry = 'mz_'+ '%.2f' % X_scale[scale_mark] 
#            if scale_entry in X_scale_IDs:
#                 X_scale_IDs.append(scale_entry+'(dup)')
#            else:
#                X_scale_IDs.append(scale_entry)
#    
#    # print 'X_scale_IDs to be returned', X_scale_IDs
#    return X_scale_IDs


if __name__ == '__main__':
    Version = 'Py3 2016-07-06'
    
    print(os.path.basename(sys.argv[0]) )
    print('Version', Version)
    
    indir = 'Tst_data'
    infname = 'BDP+Leucine+Lactose p1 positive delay 50x50 256pix 130417_1.BIF6'
    infile = os.path.join(indir, infname)
    print( infile)
    
    f = open( infile, 'rb')
    if not Read_FileID( f ):
        print( "This is not a BIF6 file")

    else:
        num_of_images, img_X_size, img_Y_size = Read_FileInfo( f )
        print( 'num_of_images, img_X_size, img_Y_size ', num_of_images, img_X_size, img_Y_size)
        for img_no in range(0, num_of_images):

            ImageIndex, Center_mass, lower_mass, upper_mass = Read_ImageInfo( f )
    ##        print 'ImageIndex, Center_mass, lower_mass, upper_mass ', ImageIndex, Center_mass, lower_mass, upper_mass

            imgX = Read_Image( f, img_X_size, img_Y_size)
            print( 'img_no, ImageIndex, Center_mass, imgX.shape ', img_no, ImageIndex, Center_mass, imgX.shape)
        

    f.close()

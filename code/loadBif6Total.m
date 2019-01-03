function bif6Im = loadBif6Total(bif6file)
%The function takes a bif6 file, read in the data into an array
% and then it sums the layers together and returns the
% total ion image as the result.
fid = fopen(bif6file);
filetype = fread(fid,[1 6],'uint8=>char');
%\
% Fileinfo header: 
% 3 WORDS, number of images, image X size, image Y size (Sizes in pixels)
%/

% Read header and parse size of image
fileinfo_N = fread(fid,[1 1],'*uint16');
fileinfo_X = fread(fid,[1 1],'*uint16');
fileinfo_Y = fread(fid,[1 1],'*uint16');
% Arrays for image data and mass data
image_raw_data = zeros(fileinfo_X,fileinfo_Y,fileinfo_N);
image_header_center_mass = zeros(1,fileinfo_N);
image_header_lower_mass = zeros(1,fileinfo_N);
image_header_upper_mass = zeros(1,fileinfo_N);
% For every separate image; read the masses for each pixel and store in arrays
for k=1:fileinfo_N
   image_header_index = fread(fid,[1 1],'*int32');
   image_header_center_mass(k) = fread(fid,[1 1],'*float');
   image_header_lower_mass(k) = fread(fid,[1 1],'*float');
   image_header_upper_mass(k) = fread(fid,[1 1],'*float');
   image_raw_data(:,:,k) = fread(fid,[fileinfo_X fileinfo_Y],'*int32');
end

% Sum all the images and return the result
im = zeros(fileinfo_X,fileinfo_Y);
for k = 1 : fileinfo_N
    im(:,:) = im(:,:) + image_raw_data(:,:,k);
end
bif6Im = im;

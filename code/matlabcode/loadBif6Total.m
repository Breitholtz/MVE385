function [bif6, bif6Im] = loadBif6Total(bif6file)
%Returns total image of bif6 file
fid = fopen(bif6file);
filetype = fread(fid,[1 6],'uint8=>char');
%\
% Fileinfo header: 
% 3 WORDS, number of images, image X size, image Y size (Sizes in pixels)
%/
fileinfo_N = fread(fid,[1 1],'*uint16');
fileinfo_X = fread(fid,[1 1],'*uint16');
fileinfo_Y = fread(fid,[1 1],'*uint16');
image_raw_data = zeros(fileinfo_X,fileinfo_Y,fileinfo_N);
image_header_center_mass = zeros(1,fileinfo_N);
image_header_lower_mass = zeros(1,fileinfo_N);
image_header_upper_mass = zeros(1,fileinfo_N);
for k=1:fileinfo_N
   image_header_index = fread(fid,[1 1],'*int32');
   image_header_center_mass(k) = fread(fid,[1 1],'*float');
   image_header_lower_mass(k) = fread(fid,[1 1],'*float');
   image_header_upper_mass(k) = fread(fid,[1 1],'*float');
   image_raw_data(:,:,k) = fread(fid,[fileinfo_X fileinfo_Y],'*int32');
   % store the image into an nD array, or a cell array, or a struct, etc.
end
im = zeros(fileinfo_X,fileinfo_Y);
for k = 1 : fileinfo_N
    
    im(:,:) = im(:,:) + image_header_center_mass(k).*image_raw_data(:,:,k);
%     im(:,:) = im(:,:) + image_raw_data(:,:,k);
end
bif6 = struct('image_raw_data',image_raw_data,'image_header_center_mass', image_header_center_mass,'image_header_lower_mass', image_header_lower_mass,'image_header_upper_mass', image_header_upper_mass, 'fileinfo_N', fileinfo_N);
bif6Im = im;
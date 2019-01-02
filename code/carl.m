run('~/Documents/MATLAB/vlfeat/toolbox/vl_setup')

%% Parse positive
fid = fopen('88Lac10BUD2MgStChalmersHiSpatBi1p1_1.BIF6');
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
%% Image processing, at the moment: Sum total
im = zeros(fileinfo_X,fileinfo_Y);
for k = 1 : fileinfo_N
%     im(:,:)= max(im(:,:),(image_header_upper_mass(k).*image_raw_data(:,:,k)));
%     im(:,:) = im(:,:) + (image_header_upper_mass(k).*image_raw_data(:,:,k));
    im(:,:) = im(:,:) + image_raw_data(:,:,k);
end

%% Parse negative
fid = fopen('88Lac10BUD2MgStChalmersHiSpatBi1n1_1.BIF6');
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
%% Image processing, at the moment: Sum total
im_n = zeros(fileinfo_X,fileinfo_Y);
for k = 1 : fileinfo_N
%     im_n(:,:)= max(im_n(:,:),(image_header_upper_mass(k).*image_raw_data(:,:,k)));
%     im_n(:,:) = im_n(:,:) + (image_header_upper_mass(k).*image_raw_data(:,:,k));
    im_n(:,:) = im_n(:,:) + image_raw_data(:,:,k);
end

%% Contrast enhancement using logistic function with different parameters and iterations

% Neccessary constants
colors = 100;
im_max = max(max(im));
im_n_max = max(max(im_n));
im_middle = (im_max + min(min(im))) / 2;
im_n_middle = (im_n_max + min(min(im_n))) / 2;
im_mean = mean(mean(im));
im_n_mean = mean(mean(im_n));
im_between_mean_and_middle = (im_middle + im_mean) / 2;
im_n_between_mean_and_middle = (im_n_middle + im_n_mean) / 2;


% Nice for enhancing fair amount of peaks and ca as many in both if steepness=0.5
steepness = 0.5;
first_logistic_im = logistic(im, im_between_mean_and_middle, im_max, steepness);
first_logistic_im_n = logistic(im_n, im_n_between_mean_and_middle, im_n_max, steepness);
first_logistic_im = logistic(first_logistic_im, im_middle, im_max, steepness);
first_logistic_im_n = logistic(first_logistic_im_n, im_n_middle, im_n_max, steepness);


% Nice enhancement for 88Lac10BUD2MgStChalmersHiSpatBi1n1_1.BIF6 if steepness=0.1
steepness = 0.1;
second_logistic_im_n = logistic(im_n, im_n_between_mean_and_middle, im_n_max, steepness);
for i=1:2
    second_logistic_im_n = logistic(second_logistic_im_n, im_n_middle, im_n_max, steepness);
    second_logistic_im_n = logistic(second_logistic_im_n, im_n_between_mean_and_middle, im_n_max, steepness);
end


% Another way to get a decent enhancement, this time in both.
steepness = 0.1;
third_logistic_im = logistic(im, im_between_mean_and_middle, im_max, steepness-0.04);
third_logistic_im_n = logistic(im_n, im_n_between_mean_and_middle, im_n_max, steepness);
for i=1:3
    % Updating middle and mean for every every iteration.
    im_middle = (im_max + min(min(third_logistic_im))) / 2;
    im_n_middle = (im_n_max + min(min(third_logistic_im_n))) / 2;
    im_mean = mean(mean(third_logistic_im));
    im_n_mean = mean(mean(third_logistic_im_n));
    im_between_mean_and_middle = (im_middle + im_mean) / 2;
    im_n_between_mean_and_middle = (im_n_middle + im_n_mean) / 2;

    third_logistic_im = logistic(third_logistic_im, im_between_mean_and_middle, im_max, steepness-0.04);
    third_logistic_im_n = logistic(third_logistic_im_n, im_n_between_mean_and_middle, im_n_max, steepness);
end


% Plots
figure(1)
imagesc(im)
title('Positive plot')
colormap(copper(colors))
colorbar

figure(2)
imagesc(im_n)
title('Negative plot')
colormap(copper(colors))
colorbar

figure(3)
imagesc(first_logistic_im)
title('Positive plot')
colormap(copper(colors))
colorbar

figure(4)
imagesc(first_logistic_im_n)
title('Negative plot')
colormap(copper(colors))
colorbar

figure(5)
imagesc(second_logistic_im_n)
title('Negative plot')
colormap(copper(colors))
colorbar

figure(6)
imagesc(third_logistic_im)
title('Positive plot')
colormap(copper(colors))
colorbar

figure(7)
imagesc(third_logistic_im_n)
title('Positive plot')
colormap(copper(colors))
colorbar


%% Feature detection and matching on original images using SIFT
imgA = im;
imgB = im_n;

% Features
[fA, dA] = vl_sift(single(imgA),'PeakThresh',1);
[fB, dB] = vl_sift(single(imgB),'PeakThresh',1);


% Plots of feature points
figure(8)
imagesc(imgA)
title('Positive plot')
colormap(copper(colors))
colorbar
hold on
vl_plotframe(fA);

figure(9)
imagesc(imgB)
title('Negative plot')
colormap(copper(colors))
colorbar
hold on
vl_plotframe(fB);

% Find matches
[matches,scores] = vl_ubcmatch(dA,dB);
xA = [fA(1,matches(1,:));fA(2,matches(1,:))];
xB = [fB(1,matches(2,:));fB(2,matches(2,:))];

figure(10)
imagesc(imgA)
title('Positive plot')
colormap(copper(colors))
colorbar
hold on
plot(xA(1,:),xA(2,:),'c.');

figure(11)
imagesc(imgB)
title('Negative plot')
colormap(copper(colors))
colorbar
hold on
plot(xB(1,:),xB(2,:),'c.');

m = length(xA);
nDOF = 4;
A = zeros(2*nDOF,9);
maxNumberOfInliers = 0;
for i = 1:10000
    randind = randperm(m,nDOF);
    for j = 1:nDOF
       A(2*j-1,:) = [xA(:,randind(j))' 1 0 0 0 -xB(1,randind(j)).*[xA(:,randind(j))' 1]];
       A(2*j,:)   = [0 0 0 xA(:,randind(j))' 1 -xB(2,randind(j)).*[xA(:,randind(j))' 1]];
    end
    
    [U,S,V] = svd(A);
    h = V(:,end);
    H = reshape(h,[3,3])';
    xB_transform = H*[xA; ones(1,m)];
    
    xTemp = xB-pflat(xB_transform);
    for j = 1:size(xB,2)
        error(j) = norm(xTemp(:,j));
    end
    inliers = error <= 5;
    numberOfInliers = nnz(inliers);
    if numberOfInliers > maxNumberOfInliers
        bestH = H;
        maxNumberOfInliers = numberOfInliers;
        bestIdx = inliers;
    end
end

%Create a transfomation that matlab can use for images 
tform = maketform('projective',bestH');
%Note: imtransform uses the transposed homography 
%Finds the bounds of the transformed image
transfbounds = findbounds(tform ,[1 1; size(imgA,2) size(imgA,1)]); 
xdata = [min([transfbounds(:,1); 1]) max([transfbounds(:,1); size(imgB,2)])]; ydata = [min([transfbounds(:,2); 1]) max([transfbounds(:,2); size(imgB,1)])]; %Computes bounds of a new image such that both the old ones will fit.
%Transform the image using bestH
[newImgA] = imtransform(imgA,tform,'xdata',xdata,'ydata',ydata);
tform2 = maketform('projective',eye(3));
[newImgB] = imtransform(imgB,tform2,'xdata',xdata,'ydata',ydata,'size',size(newImgA)); %Creates a larger version of B
newAB = newImgB;
newAB(newImgB < newImgA) = newImgA(newImgB < newImgA);
%Writes both images in the new image. 
%(A somewhat hacky solution is needed 
%since pixels outside the valid image area are not allways zero...)

% Plot morphed image
figure(12)
imagesc(newAB)
colormap(copper(colors))
colorbar
title('Panorama plot of the two images')

%% Contrast enhancement for morphed image, using the last method
width = size(newAB,2);
height = size(newAB,1);
x_offset = width - size(imgA,2) + 25;
y_offset = height - size(imgA,1) + 25;
cropped_newAB = newAB(y_offset:(height-y_offset), x_offset:(width-x_offset));

maxx = max(max(cropped_newAB));
middlee = (maxx + min(min(cropped_newAB))) / 2;
meann = mean(mean(cropped_newAB));
between_mean_and_middle = (middlee + meann) / 2;

steepness = 0.08;
logistic_cropped_newAB = logistic(cropped_newAB, between_mean_and_middle, maxx, steepness);
for i=1:2
    maxx = max(max(cropped_newAB));
    middlee = (maxx + min(min(cropped_newAB))) / 2;
    meann = mean(mean(cropped_newAB));
    between_mean_and_middle = (middlee + meann) / 2;
    logistic_cropped_newAB = logistic(logistic_cropped_newAB, between_mean_and_middle, maxx, steepness);
end

figure(13)
imagesc(logistic_cropped_newAB)
colormap(copper(colors))
colorbar
title('Panorama plot of the two images')

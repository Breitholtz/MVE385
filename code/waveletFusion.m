close all
clear
clc
%% Read Images
% the size of images must be equal
[file, pathname] = uigetfile('*.mat','Load Image 1 ');cd(pathname);
load(file);
[dataSize, nSpectr] = size(DATA);
imageDim = sqrt(dataSize);
a = zeros(imageDim,imageDim,5);
for i = 1 : 5
    a(:,:,i) = vec2mat(DATA(:,i),imageDim);
end
% a = multibandread('DATA.mat',[imageDim,imageDim,nSpectr],'double',0,'bsq','ieee-be');
%%
[file, pathname] = uigetfile('*.mat','Load Image 2 ');cd(pathname);
load(file);
[dataSize, nSpectr] = size(DATA);
imageDim = sqrt(dataSize);
b = zeros(imageDim,imageDim,5);
for i = 1 : 5
    b(:,:,i) = vec2mat(DATA(:,i),imageDim);
end
%%
c = zeros(imageDim,imageDim,5);
for layer = 1 : 5
    %%   Wavelet Transform
    [a1,b1,c1,d1]=dwt2(a(:,:,layer),'db2');
    [a2,b2,c2,d2]=dwt2(b(:,:,layer),'db2');
    [k1,k2]=size(a1);
    %% Fusion Rules
    %% Average Rule
    for i=1:k1
        for j=1:k2
            a3(i,j)=(a1(i,j)+a2(i,j))/2;
        end
    end
    %% Max Rule
    for i=1:k1
        for j=1:k2
            b3(i,j)=max(b1(i,j),b2(i,j));
            c3(i,j)=max(c1(i,j),c2(i,j));
            d3(i,j)=max(d1(i,j),d2(i,j));
        end
    end
    %% Inverse Wavelet Transform
    c(:,:,layer)=idwt2(a3,b3,c3,d3,'db2');
end
%% Imshow

imshow(a(:,:,1))
title('First Image')
figure,imshow(b(:,:,1))
title('Second Image')
figure,imshow(c(:,:,1),[])
title('Fused Image')
%% Performance Criteria
CR1=corr2(a(:,:,1),c(:,:,1));
CR2=corr2(b(:,:,1),c(:,:,1));
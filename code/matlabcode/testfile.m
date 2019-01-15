clc
close all
% [a1,b1,c1,d1]=dwt2(posimage,'db2');
% [a2,b2,c2,d2]=dwt2(negimage,'db2');
% posimage = double(imread('proffe1.jpg'));
% negimage = double(imread('proffe2.jpg'));
% posimage(1 : 20, 1 : 20) = 0;
% matching = hyperspectral_wavelet_similarities(posimage,negimage);
significant_level = 0.1;
similarities = image_similarities_hypothesis_testing(posimage,negimage,6,significant_level);
m_pos = similarities.*posimage;
m_neg = similarities.*negimage;
matching = (hyperspectral_image_fusion_wavelet(m_pos,m_neg));
subplot(1,3,1)
% figure
imagesc(matching);
title('Fused image')
colorbar

subplot(1,3,2)
% figure
imagesc((negimage));
title('Negative image')
colorbar
subplot(1,3,3)
% figure
imagesc((posimage));
title('Positive image')
colorbar
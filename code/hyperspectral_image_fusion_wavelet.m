function [fused_image, quality_score] = hyperspectral_image_fusion_wavelet(hyper_image1, hyper_image2)
% pictures have to have the same size
[height, width, nbr_spect] = size(hyper_image1);
fused_image = zeros(height, width, nbr_spect);
% fuse each spectrum
for spect = 1 : nbr_spect
    % Get maximum decomposition level
%     L1 = wmaxlev(hyper_image1(:,:,spect),'haar');
%     L2 = wmaxlev(hyper_image2(:,:,spect),'haar');
%     decomp_level = min(L1,L2);
    decomp_level = 5;
    fused_max_max = wfusimg(hyper_image1(:,:,spect),hyper_image2(:,:,spect),'haar',decomp_level,'max','max');
    % To do: perform fusion with several different settings and return
    % picure with best quality
    fused_image(:,:,spect) = fused_max_max;
end
quality_score = 1;
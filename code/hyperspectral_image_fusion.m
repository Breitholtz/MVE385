function [sharpness_improvement, fused_total_image, positive_struct, negative_struct, transform] = hyperspectral_image_fusion(...
    string_positive_image, string_negative_image)
% Type == total
[bif6_negative, image_negative_total] = loadBif6Total(string_negative_image);
[bif6_positive, image_positive_total] = loadBif6Total(string_positive_image);

[fused_positive, fused_negative, transform] = SIFTfusion(image_positive_total, image_negative_total);
%Transform mapps positive image to negative image. 
% Compute the union
fused_image = fused_positive + fused_negative;

% Inverse transform
% Positive
tform = maketform('projective', inv(transform));
transfbounds = findbounds(tform ,[1 1; size(image_positive_total,2) size(image_positive_total,1)]);
inversed_fused_positive = imtransform(fused_positive,tform,'xdata',...
    [1, size(image_positive_total,2)],...
    'ydata', [1, size(image_positive_total,1)]);

%Negative
tform = maketform('projective', eye(3));
transfbounds = findbounds(tform ,[1 1; size(image_negative_total,2) size(image_negative_total,1)]);
inversed_fused_negative = imtransform(fused_negative,tform,'xdata',...
    [1, size(image_negative_total,2)],...
    'ydata', [1, size(image_negative_total,1)]);

%Cropped images
% Cropped positive
row  = find(~all(inversed_fused_positive == 0,2));
col = find(~all(inversed_fused_positive == 0,1));
size(row)
size(col)
cropped_fused_positive = inversed_fused_positive(row(1):row(end), col(1):col(end));
size(cropped_fused_positive)
fused_positive_raw_data = bif6_positive.image_raw_data(row(1):row(end), col(1):col(end),:);

% Cropped negative
row  = find(~all(inversed_fused_negative == 0,2));
col = find(~all(inversed_fused_negative == 0,1));
cropped_fused_negative = inversed_fused_negative(row(1):row(end), col(1):col(end));
fused_negative_raw_data = bif6_negative.image_raw_data(row(1):row(end), col(1):col(end),:);

% Cropped fused
row  = find(~all(fused_image == 0,2));
col = find(~all(fused_image == 0,1));
cropped_fused_image =  fused_image(row(1):row(end), col(1):col(end));

%Sharpness
mean_positive = mean(image_positive_total,'all');
mean_negative = mean(image_negative_total,'all');
mean_fused = mean(cropped_fused_image,'all');

sharpness_positive = immse(image_positive_total, mean_positive * ones(size(image_positive_total)));
sharpness_negative = immse(image_negative_total, mean_negative * ones(size(image_negative_total)));
sharpness_fused = immse(cropped_fused_image, mean_fused * ones(size(cropped_fused_image)));

eps = 0.000001; % Avoid divison with zero

sharpness_improvement = sharpness_fused / ( (sharpness_negative + sharpness_positive) + eps);


% To "bif6"
positive_struct = bif6_positive;
positive_struct.image_raw_data = fused_positive_raw_data;

negative_struct = bif6_negative;
negative_struct.image_raw_data = fused_negative_raw_data;

fused_total_image = cropped_fused_image;

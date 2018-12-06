function matching_regions = image_similarities_hypothesis_testing(hyper_image1, hyper_image2,threshold,significant_level)
% images must have the same size
%
[height, width, depth] = size(hyper_image1);

new_hyper_image1 = zeros(height,width,depth);
new_hyper_image2 = new_hyper_image1;

matching_regions = zeros(height, width, depth);

% Set window-sizes
height_divisors = divisors(height);
width_divisors = divisors(width);
% %height or width is a prime nbr, To do: extend picture so we can analyze
% %this case
% if length(height_divisors) <= 2 || length(width_divisors) <= 2
%     disp('image size is a prime, analysis not possible')
%     return(1)
% end

% Restrict nbr of windows, we don't need window 1x1 and window heightxwidth
if length(height_divisors) > threshold
    height_divisors = height_divisors(1:threshold - 1);
else
    height_divisors = height_divisors(1:end-1);
end

% For now, assume that height = width
if length(width_divisors) > threshold
    width_divisors = width_divisors(1:threshold- 1 );
else
    width_divisors = width_divisors(1:end-1);
end


for d = 1 : depth
    hyper_image1(:,:,d) = normalize(hyper_image1(:,:,d));
    hyper_image2(:,:,d) = normalize(hyper_image2(:,:,d));
    for k = 1 : length(height_divisors)
        for q = 1 : length(width_divisors)
            window = [height_divisors(k), width_divisors(q)];
            % Slide window
            for i = 1 : window(1) : height - window(1)
                for j = 1 : window(2) : width - window(2)
                    window_image1 = hyper_image1(i : i + window(1), j : j + window(2) , d);
                    window_image2 = hyper_image2(i : i + window(1), j : j + window(2) , d);
                    [h,w] = size(window_image1);
                    window_vector1 = reshape(window_image1, [1 h*w]);
                    window_vector2 = reshape(window_image2, [1 h*w]);
%                     h = kstest2(window_vector1, window_vector2, 'Alpha', significant_level);
                    h = (corr2(window_vector1, window_vector2)) < significant_level;
                    % If the pixels seems to be generated from the same
                    % distribution i.e the same object
                    if h == 0
                        matching_regions(i : i + window(1), j : j + window(2), d) = 1;                    end
                end
            end
        end
    end
end
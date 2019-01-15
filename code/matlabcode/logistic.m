function output = logistic(x, midpoint, maxValue, steepness)
% function which returns the value of the logistic function with the given parameters.
% This is used to increase the contrast of images
    output = maxValue ./ (1 + exp(-steepness .* (x - midpoint)));

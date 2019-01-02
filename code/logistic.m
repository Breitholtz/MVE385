function output = logistic(x, midpoint, maxValue, steepness)

    output = maxValue ./ (1 + exp(-steepness .* (x - midpoint)));
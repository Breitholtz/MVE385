function x = pflat(X)

    lastElement = X(end,:);
    x = X./lastElement;
    x(end,:) = [];
end






function f=imquality(I)
%
% image quality function; takes an image in array format.
% It should be noted that the value that is used to define an 'important' pixel
% in this program is arbitrary and can be tuned to some value that gives more meaningful values for the type of image used. 
%
N=size(I,1);
M=size(I,2);
K=size(I,3);

% takes the FFT of both images and centers the spectrum for each
for k=1:K
F=fft(I(:,:,k));
Fcenter=fftshift(F);
F2=fft(I2(:,:,k));
Fcenter2=fftshift(F2);

% find the maximum value in each spectra
M1=max(max(abs(Fcenter)));
M2=max(max(abs(Fcenter2)));

% loop over every pixel and see if it is larger than the maxvalue over 1000
% If it is then we assume that it is an 'important' pixel and count it as such.
% We then use the quotient of 'important' pixels over the number of pixels as our metric
T_h1=0;
T_h2=0;
for i=1:N
    for j=1:M
        if (abs(Fcenter(i,j))>M1/1000)
            T_h1=T_h1+1;
        end
        if (abs(Fcenter2(i,j))>M2/1000)
            T_h2=T_h2+1;
        end
    end
end
% Save the value of the metric for each layer in our image and proceed to the next.
disp('high res: layer'+ k);
high(k)=T_h1/(N*M);
disp('low res: layer'+k);
low(k)=T_h2/(N*M);
end
% One could use the means below as some sort of overall measure of quality
%mean(high)
%mean(low)
end

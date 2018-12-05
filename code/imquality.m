function f=imquality(I,I2)
%
% image quality function; takes two images of identical size atm.
%
N=size(I,1);
M=size(I,2);
K=size(I,3);

for k=1:K
F=fft(I(:,:,k));
Fcenter=fftshift(F);
F2=fft(I2(:,:,k));
Fcenter2=fftshift(F2);

M1=max(max(abs(Fcenter)));
M2=max(max(abs(Fcenter2)));
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

disp('high res: layer'+ k);
high(k)=T_h1/(N*M);
disp('low res: layer'+k);
low(k)=T_h2/(N*M);
end
mean(high)
mean(low)
end

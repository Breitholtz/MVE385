function f=imquality(I,I2)
%
% image quality function
%
for k=1:3
F=fft(I(:,:,k));
Fcenter=fftshift(F);
F2=fft(I2(:,:,k));
Fcenter2=fftshift(F2);

M=max(max(abs(Fcenter)));
M2=max(max(abs(Fcenter2)));
T_h1=0;
T_h2=0;
for i=1:size(I(:,1,1))
    for j=1:size(I(1,:,1))
        if (abs(Fcenter(i,j))>M/1000)
            T_h1=T_h1+1;
        end
        if (abs(Fcenter2(i,j))>M2/1000)
            T_h2=T_h2+1;
        end
    end
end

disp('high res: layer'+ k);
high(k)=T_h1/(size(I(:,1,1),1).*size(I(1,:,1),2));
disp('low res: layer'+k);
low(k)=T_h2/(size(I(:,1,1),1).*size(I(1,:,1),2));
end
mean(high)
mean(low)
end
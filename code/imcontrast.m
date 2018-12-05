%function f=imcontrast(I)

% root mean square contrast

I=posimage;
N=size(I,1);
M=size(I,2);

Ibar=mean2(I);

sum=0;
for i=1:N
	for j=1:M
		sum=sum+(I(i,j)/Ibar-1)^2;
	end
end
sum=sum/(N*M);
disp(sum);
result=sqrt(sum);

disp(result);
%end



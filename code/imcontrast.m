function f=imcontrast(I)

% root mean square contrast

N=size(I,1);
M=size(I,2);

Ibar=mean(I);

sum=0;
for i=1:N
	for j=1:M
		sum+=(I(i,j)/Ibar-1)^2;
	end
end
result=sqrt(sum);

disp(result);
end



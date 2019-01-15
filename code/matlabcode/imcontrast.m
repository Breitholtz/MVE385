%function f=imcontrast(I)

% Function computing the root mean square measure of the contrast of the given image.

% 
I=posimage;
N=size(I,1);
M=size(I,2);

Ibar=mean2(I);

% computing mean square error and displaying result
sum=0;
for i=1:N
	for j=1:M
		sum=sum+(I(i,j)-Ibar)^2;
	end
end
sum=sum/(N*M);
disp(sum);
result=sqrt(sum);

disp(result);
end



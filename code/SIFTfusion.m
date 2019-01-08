function [fusedP, fusedN, transform] = SIFTfusion(im_p, im_n, steepness)
% Positive projected onto negative

im_max = max(max(im_p));
im_n_max = max(max(im_n));
im_middle = (im_max + min(min(im_p))) / 2;
im_n_middle = (im_n_max + min(min(im_n))) / 2;
im_mean = mean(mean(im_p));
im_n_mean = mean(mean(im_n));

imgA = im_p;
imgB = im_n;

% Features
[fA, dA] = vl_sift(single(imgA),'PeakThresh',1);
[fB, dB] = vl_sift(single(imgB),'PeakThresh',1);


% Find matches
[matches,scores] = vl_ubcmatch(dA,dB);
xA = [fA(1,matches(1,:));fA(2,matches(1,:))];
xB = [fB(1,matches(2,:));fB(2,matches(2,:))];

m = length(xA);
nDOF = 4;
A = zeros(2*nDOF,9);
maxNumberOfInliers = 0;
for i = 1:10000
    randind = randperm(m,nDOF);
    for j = 1:nDOF
       A(2*j-1,:) = [xA(:,randind(j))' 1 0 0 0 -xB(1,randind(j)).*[xA(:,randind(j))' 1]];
       A(2*j,:)   = [0 0 0 xA(:,randind(j))' 1 -xB(2,randind(j)).*[xA(:,randind(j))' 1]];
    end
    
    [U,S,V] = svd(A);
    h = V(:,end);
    H = reshape(h,[3,3])';
    xB_transform = H*[xA; ones(1,m)];
    
    xTemp = xB-pflat(xB_transform);
    for j = 1:size(xB,2)
        error(j) = norm(xTemp(:,j));
    end
    inliers = error <= 5;
    numberOfInliers = nnz(inliers);
    if numberOfInliers > maxNumberOfInliers
        bestH = H;
        maxNumberOfInliers = numberOfInliers;
        bestIdx = inliers;
    end
end

%Create a transfomation that matlab can use for images 
tform = maketform('projective',bestH');
%Note: imtransform uses the transposed homography 
%Finds the bounds of the transformed image
transfbounds = findbounds(tform ,[1 1; size(imgA,2) size(imgA,1)]); 
xdata = [min([transfbounds(:,1); 1]) max([transfbounds(:,1); size(imgB,2)])]; ydata = [min([transfbounds(:,2); 1]) max([transfbounds(:,2); size(imgB,1)])]; %Computes bounds of a new image such that both the old ones will fit.
%Transform the image using bestH
[newImgA] = imtransform(imgA,tform,'xdata',xdata,'ydata',ydata);
tform2 = maketform('projective',eye(3));
[newImgB] = imtransform(imgB,tform2,'xdata',xdata,'ydata',ydata,'size',size(newImgA)); %Creates a larger version of B
% newAB = newImgB;
% newAB = newImgA + newImgB;
% newAB = newImgA.*(newImgB>0) + newImgB.*(newImgA>0);
fusedP = newImgA.*(newImgB>0);
fusedN = newImgB.*(newImgA>0);
% newAB(newImgB < newImgA) = newImgA(newImgB < newImgA);
%Writes both images in the new image. 
%(A somewhat hacky solution is needed 
%since pixels outside the valid image area are not allways zero...)

% fusedIm = newAB;
transform = bestH';
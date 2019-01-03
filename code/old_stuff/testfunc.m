load('88Lac10BUD2MgStChalmersBi1HiMassn1_1-v73.mat')
Dataneg=DATA;
varneg=VARID2;
load('88Lac10BUD2MgStChalmersBi1HiMassp1_1-v73.mat')
Datapos=DATA;
varpos=VARID2;

map(1)=max(varpos(1),varneg(1));
j=2;
i=2;
k=1;
while(i<=241 && j<=225)
    if varpos(i)<= map(k)
        i=i+1;
    elseif varneg(j)<=map(k)
        j=j+1;
    else
        k=k+1;
        map(k)=max(varpos(i),varneg(j));%remove spectrum who does not exist for both(large)
    end
end
%%
map(1)=0;%%special case
k=2;
i=2;
mappos(1,1)=2;%special cases
mappos(2,1)=1;%special cases
while(i<=241 && k<=158)
    if varpos(i)<=map(k)
        mappos(1,i)=k;
            if varpos(i-1)>=map(k-1)
                mappos(2,i)=1;
            else
                mappos(2,i)=(varpos(i)-map(k-1))/(varpos(i)-varpos(i-1)); %assume max value
            end
        i=i+1;
    else
        k=k+1;
    end
end
%%
k=2;
i=2;
mapneg(1,1)=2;%special cases
mapneg(2,1)=1;%special cases
while(i<=225 && k<=158)
    if varneg(i)<=map(k)
        mapneg(1,i)=k;
            if varneg(i-1)>=map(k-1)
                mapneg(2,i)=1;
            else
                mapneg(2,i)=(varneg(i)-map(k-1))/(varneg(i)-varneg(i-1)); %assume max value
            end
        i=i+1;
    else
        k=k+1;
    end
end

%% shift spectrum
ld=length(DATA);
Datafixneg=zeros(ld,158);
Datafixpos=zeros(ld,158);
for i=1:ld
    for j=1:length(mapneg)
        k=mapneg(1,j);
        pros=mapneg(2,j);
        Datafixneg(i,k)=Datafixneg(i,k) + Dataneg(i,j)*pros;
            if pros<1
                Datafixneg(i,k-1)=Datafixneg(i,k-1) + Dataneg(i,j)*(1-pros);
            end
    end
end

for i=1:ld
    for j=1:length(mappos)
        k=mappos(1,j);
        pros=mappos(2,j);
        Datafixpos(i,k)=Datafixpos(i,k) + Datapos(i,j)*pros;
            if pros<1
                Datafixpos(i,k-1)=Datafixpos(i,k-1) + Datapos(i,j)*(1-pros);
            end
    end
end

Datafixneg(:,2)=0; %temporary
%% todo average out
mat2 =[Datafixpos*mean2(Datafixneg)/mean2(Datafixpos); Datafixneg];
%mat2 =[Datafixneg;Datafixpos*mean2(Datafixneg)/mean2(Datafixpos)];
[matpca2,scores2,latency2,tsquared2,explained2] = pca(mat2,'Centered',false);%pca two components

[pospca1,scorespos,latencypos,tsquaredpos,explainedpos] = pca(Datafixneg,'Centered',false);
[negpca1,scoresneg,latencyneg] = pca(Datafixpos-mean2(Datafixpos),'Centered',false);
%%

comp=1;%1
W=sqrt(32768/2);
pcapos=scores2(1:32768/2,comp);
pcaneg=scores2(32768/2+1:32768,comp);
posimage=reshape(pcapos,[W,W]);
negimage=reshape(pcaneg,[W,W]);
%imagesc(posimage) %% image
imagesc(negimage)
%% todo emil code.
%% cross correlation see if neg[1,1] pos[1,1] are positive effect, 0 otherwise assume mean mean2(neg)
fusimage= zeros(128);
muneg=mean(pcaneg);
mupos=mean(pcapos);
vneg=var(pcaneg);
vpos=var(pcapos);

for i=1:128
    for j=1:128
        if (negimage(i,j)-muneg)*(posimage(i,j)-mupos)>0
            if (negimage(i,j)-muneg)<0
                fusimage(i,j)=-((negimage(i,j)-muneg)*(posimage(i,j)-mupos))/(vneg*vpos);
            else
                fusimage(i,j)=((negimage(i,j)-muneg)*(posimage(i,j)-mupos))/(vneg*vpos);
            end
        end
    end
end
imagesc(fusimage)
colorbar
%%
ifp=zeros(128);
sum=-fusimage;
ind=zeros(128);

for i=-2:2
    for j=-2:2
        sum=sum+circshift(fusimage,[i,j]);
    end
end

for i=-2:2
    for j=-2:2
        ind=ind+(circshift(fusimage,[i,j])~=0);%negative/positive or both matters?
    end
end
mean2(ind);%mean around 12
ind=(ind>12);

primeimg=sum.*fusimage;
ifp=ind.*primeimg.*(primeimg>0).*sign(negimage-muneg);
imagesc(ifp)
colorbar

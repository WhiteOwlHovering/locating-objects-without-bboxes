% Example

load('mall_gt.mat');

img_name = '/home/UCSTAFF.WIN.CANBERRA.EDU.AU/s436241/Documents/mall_dataset/frames/seq_%.6d.jpg';

img_index = 350;

im = imread(sprintf(img_name,img_index));

XY=frame{img_index}.loc;

imshow(im); hold on;
plot(XY(:,1),XY(:,2),'r*');
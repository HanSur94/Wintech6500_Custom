clear all;
imagename = 'test_images_numbered_rgb/test_image_1.png';
B = imread(imagename);
A = uint8(imbinarize(B)*255);
imagename = [imagename(1,1:end-3),'bmp'];
imwrite(A,imagename);
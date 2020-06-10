clear all;
imagename = 'test_images_numbered_rgb/test_image_5.png';
B = imread(imagename);
A = imbinarize(B);
imagename = [imagename(1,1:end-3),'bmp'];
imwrite(A,imagename);
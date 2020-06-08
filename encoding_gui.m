function encoding_gui()
%ENCODING_GUI() - Creates a minimalistic GUI for easy encoding.
% This function will create and handle a simple GUI in order to encode
% images. Encoding will be done using the enhanced run length encoding
% recommended by the DLPC900 Programming Guide. The encoding is done by
% using functions from Klaus Huecks DMDConncet library.
%
% Syntax: encoding_gui()
% 
% Input:
%       none  
%
% Output:
%       none
%
% Author: Hannes Suhr, credits to Klaus Hueck
% Hochschule Aalen
% Email address: hannes.suhr@studmail.htw-aalen.de  
% Website: -
% June 2020; Last revision: 08-June-2020

    % prealloc variables
    f = [];
    directory_button = [];
    encoding_button = [];
    textField = [];
    encoded = [];
    files = [];
    directoryName = [];
    fontSize = 13;
    
    function createGui()
    % CREATEGUI - CReates the figure handle for our Gui.
        f = figure('Name','Encode Images','DockControls','off',...
            'Visible','off','Position',[500,500,450,100],...
            'MenuBar','none');
    end
    
    function createWidgtes()
    %CREATEWIDGETS - Constructs the Gui widgets.   
        directory_button = uicontrol('Style','pushbutton',...
                 'String','Directory',...
                 'Position',[10,10,90,90],...
                 'Callback',{@directory_button_Callback},...
                 'FontSize',fontSize);
             
        encoding_button = uicontrol('Style','pushbutton',...
                 'String','Encode',...
                 'Position',[100,10,90,90],...
                 'Callback',{@encoding_button_Callback},...
                 'FontSize',fontSize);
             
        textField = uicontrol('Style','text','Position',[200,10,180,70]);
   
        align([directory_button,encoding_button, textField],...
            'distribute','bottom');
        f.Visible = 'on';
    end
    
    function directory_button_Callback(~,~)
    %DIRECTORY_BUTTON_CALLBACK - Button function fetching the directory.
        directoryName = uigetdir('./',...
            'Select Image Directory For Encoding');
        %disp(directoryName)
        files = dir(join([directoryName,'/*.bmp']));
        updateTextField(sprintf('Found %d images.\n',length(files)));
        encoded = cell(length(files),1);
    end

    function encoding_button_Callback(~,~)
    %ENCODING_BUTTON_CALLBACK - Button function, encodes the images and
    %saves them.
        tic;
        for iFiles = 1:length(files)
            updateTextField(sprintf('encode image %s %d',...
                files(iFiles).name,iFiles));
           % disp(join([directoryName,'/',files(iFiles).name]));
            image = imread(join([directoryName,'/',files(iFiles).name]));
            encoded{iFiles} = enhancedRLE(8,image);
        end
        
        encodedFileName = 'encoded_images.txt';
        disp(encoded)
        writecell(encoded, join([directoryName,'/',encodedFileName]),...
            'Delimiter', ',');
        updateTextField(sprintf(...
            'Encoding done after %.3f [s]. Saved Encoding in %s.',...
            toc,encodedFileName));
    end

    function updateTextField(formattedText)
    %UPDATETEXTFIELD - Shows the current status in the Gui.
        set(textField,'String',formattedText);
        set(textField,'FontSize',13);
        drawnow;
        disp(formattedText)
    end

    % Start the gui
    createGui();
    createWidgtes();
end

function encoded_string = enhancedRLE(bitDepth, bitmap)
%enhancedRLE compresses a bitmap. 
% enhancedRLE uses the enhance run length encoding according ot the DLPC900
% programming guide, and attaches the needed header file to the compressed
% data.
%
% Syntax: encoded_string = enhancedRLE(bitDepth, bitmap)
% 
% Input:
%       bitDepth -  The bit depth that is used to encode the image. It
%                   should be set to the bit depth of the images.
%       bitmap   -  The bitmap that we encode as a matrix.  
%
% Output:
%       encoded_string  -   The encoded data as a string. each byte is
%                           represented in hexadecimal.
%
% The RLE algorithm is based on http://stackoverflow.com/questions/
% 12059744/run-length-encoding-in-matlab
% 
% Author: Klaus Hueck (e-mail: khueck (at) physik (dot) uni-hamburg (dot) de)
% Version: 0.0.1alpha
% Changes tracker:  28.01.2016  - First version
% License: GPL v3

    signature = ['53'; '70'; '6C'; '64'];
    imageWidth = dec2hex(typecast(uint16(size(bitmap,2)),'uint8'),2);
    imageHeight = dec2hex(typecast(uint16(size(bitmap,1)),'uint8'),2);
    numOfBytes = dec2hex(typecast(uint32(size(bitmap,1)*size(bitmap,2)*...
        bitDepth),'uint8'),2);
    backgroundColor = ['00'; '00'; '00'; '00'];
    compression = '02';

    header = [signature; imageWidth; imageHeight; numOfBytes; ...
        'FF'; 'FF'; 'FF'; 'FF'; 'FF'; 'FF'; 'FF'; 'FF'; backgroundColor; ...
        '00'; compression; '01'; '00'; '00'; '00'; '00'; '00'; '00'; '00';...
        '00'; '00'; '00'; '00'; '00'; '00'; '00'; '00'; '00'; '00'; '00';...
        '00'; '00'; '00'];

    % convert input matrix to decimal and transpose for later handling
    bitmap = bitmap'*1; 

    % expand to 24bit in 3x8bit decimal notation
    BMP24 = dec2hex(bitmap(:),6);

    % clear return variable
    [szy, szx] = size(bitmap);
    encoded_string = '';
    %encoded_string = strings(1,imageWidth*imageHeight);
    %encoded_string = repmat('a',1,szx*10);

    % reshape in order to get 24bit pixel information line by line
    for i = 1:szx
        [~, ~, ic] = unique(BMP24((i-1)*szy+1:i*szy,:), 'rows');
        ind = find(diff([ic(1)-1, ic(:)']))+(i-1)*szy;
        relMat = [formatrep(diff([ind, i*szy+1])), BMP24(ind,:)];
        encoded_string = [encoded_string sprintf(relMat(:,:)')];
        %encoded_string(1,1+(i-1)*10:i*10) = sprintf(relMat(:,:)');
    end
    encoded_string = [header; char(regexp(encoded_string,...
        sprintf('\\w{1,%d}', 2), 'match')'); '00'; '01'; '00'];
    encoded_string = hex2dec(encoded_string);
end


function x = formatrep(n)
%FORMATREP returns the eRLE repetition number n in required format.
% According to the DLPC900 programmers guide p.64, the repetition byte n for
% the enhanced run length encoding has to be in the form 
% n < 128  : x = n
% n >= 128 : x = [(n & 0xfF ) | 0x80, (n >> 7)]
% here, &, | and >> are the corresponding operators in C syntax. 
% Be careful, the example featured in the programmers guide seems to be
% wrong!
% For reference and to play around you can use the following C code:
% #include <stdio.h>
% int main()
% {
%     int x = 0;
%     int y = 0;
%     int z = 500;
%     x = ( z & 0x7F ) | 0x80;
%     y = z >> 7;
%     printf("%x, %x \n", x & 0xff, y & 0xff);
%     printf("%d, %d \n", x, y);
%     return 0;
% }
%
% Syntax: x = formatrep(n)
% 
% Input:
%       n -  The repetition number, when encoding.
%
% Output:
%       x -  The repetition number in the correct format. 
%
% Author: Klaus Hueck (e-mail: khueck (at) physik (dot) uni-hamburg (dot) de)
% Version: 0.0.1alpha
% Changes tracker:  28.01.2016  - First version
% License: GPL v3
%
% This function was copied from the DMDConnect library from Klaus Hueck.
% Repository: https://github.com/deichrenner/DMDConnect
% DOI: 10.5281/zendo.45713

    if n < 128
        x = dec2hex(n, 2);
    else
        x1 = dec2hex(bitor(bitand(n,127), 128), 2);
        x2 = dec2hex(bitshift(n, -7), 2);
        x = [x1, x2];
    end

end
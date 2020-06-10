classdef encoding_gui < handle
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
    % June 2020; Last revision: 09-June-2020
    
    properties (Access = private)
        guiFigure;                  % the figure handle
        directory_button;           % select directory button
        encoding_button;            % start encoding button
        textField;                  % text field to show status
        encoded;                    % encoded data
        files;                      % image files to encode
        directoryName;              % directory name to save encoded
        fontSize = 13;              % font size of the gui
        encodedFileName =...        % name of file with encoded data
            'encoded_images.txt';
    end
    
    methods
        function obj = encoding_gui()
            % CREATEGUI - Creates Gui object
            
            obj.guiFigure = figure('Name','Encode Images','DockControls','off',...
                'Visible','off','Position',[500,500,450,100],...
                'MenuBar','none');
            % Start the gui
            obj.createWidgtes();
        end
        
        function obj = createWidgtes(obj)
            %CREATEWIDGETS - Constructs the Gui widgets.
            
            obj.directory_button = uicontrol('Style','pushbutton',...
                'String','Directory',...
                'Position',[10,10,90,90],...
                'Callback',{@obj.directory_button_Callback},...
                'FontSize',obj.fontSize);
            
            obj.encoding_button = uicontrol('Style','pushbutton',...
                'String','Encode',...
                'Position',[100,10,90,90],...
                'Callback',{@obj.encoding_button_Callback},...
                'FontSize',obj.fontSize);
            
            obj.textField = uicontrol('Style','text','Position',...
                [200,10,180,70]);
            
            align([obj.directory_button, obj.encoding_button,...
                obj.textField],'distribute','bottom');
            obj.guiFigure.Visible = 'on';
        end
        
        function directory_button_Callback(obj, ~, ~)
            %DIRECTORY_BUTTON_CALLBACK - Button function fetching the directory.
            
            % get the directory name
            obj.directoryName = uigetdir('./',...
                'Select Image Directory For Encoding');
            
            % get all images with the specified extensions from directory
            obj.files = dir(join([obj.directoryName,'/*.bmp']));
            
            % show how many images where found
            obj.updateTextField(sprintf('Found %d images.\n',...
                length(obj.files)));
            
            % create cell array based on the number of cells found
            obj.encoded = cell(length(obj.files)*2,1);
        end
        
        function encoding_button_Callback(obj, ~, ~)
            %ENCODING_BUTTON_CALLBACK - Button function, encodes the images and
            %saves them.
            
            % overwrite cell once in the beginning if it already exist
            writecell({''},...
                    join([obj.directoryName,'/',obj.encodedFileName]),...
                'Delimiter', ',','WriteMode','overwrite');
            
            % for each image, do encoding & save it in the
            tic;
            for iFiles = 1:1:length(obj.files)
                
                % update textbox in gui
                obj.updateTextField(sprintf('encode image %s %d',...
                    obj.files(iFiles).name,iFiles));
                
                % get full image name
                imageName = join([obj.directoryName,'/',obj.files(iFiles).name]);
                image = imread(imageName);
                obj.encoded{iFiles*2-1} = join(obj.files(iFiles).name,'\n');
                obj.encoded{iFiles*2} = enhancedRLE(8,image);
            end
            writecell(obj.encoded,...
                        join([obj.directoryName,'/',obj.encodedFileName]),...
                    'Delimiter', ',','WriteMode','append');

            obj.updateTextField(sprintf(...
                'Encoding done after %.3f [s]. Saved Encoding in %s.',...
                toc,obj.encodedFileName));
        end
        
        function updateTextField(obj, formattedText)
            %UPDATETEXTFIELD - Shows the current status in the Gui.
            
            set(obj.textField,'String',formattedText);
            set(obj.textField,'FontSize',obj.fontSize);
            drawnow;
            disp(formattedText)
        end
    end
    
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
%
% This function was copied from the DMDConnect library from Klaus Hueck.
% Repository: https://github.com/deichrenner/DMDConnect
% DOI: 10.5281/zendo.45713

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

function writecell(C, filename, varargin)
%WRITECELL Write a cell array to a file.
%   WRITECELL(C) writes the cell array C to a comma-delimited text
%   file. The file name is the workspace name of the cell array C,
%   appended with '.txt'. If WRITECELL cannot construct the file name
%   from the homogenous array input, it writes to the file 'cell.txt'.
%   WRITECELL overwrites any existing file.
%
%   WRITECELL(C,FILENAME) writes the cell array C to the file
%   FILENAME as column-oriented data. WRITECELL determines the file
%   format from its extension. The extension must be one of those listed
%   below.
%
%   WRITECELL(C,FILENAME,'FileType',FILETYPE) specifies the file type,
%   where FILETYPE is one of 'text' or 'spreadsheet'.
%
%   WRITECELL writes data to different file types as follows:
%
%   .txt, .dat, .csv:  Delimited text file (comma-delimited by default).
%
%          WRITECELL creates a column-oriented text file, i.e., each
%          column of each variable in C is written out as a column in the
%          file.
%
%          Use the following optional parameter name/value pairs to control
%          how data are written to a delimited text file:
%
%          'Delimiter'      The delimiter used in the file. Can be any of ' ',
%                           '\t', ',', ';', '|' or their corresponding names 'space',
%                           'tab', 'comma', 'semi', or 'bar'. Default is ','.
%
%          'QuoteStrings'   A logical value that specifies whether to write
%                           text out enclosed in double quotes ("..."). If
%                           'QuoteStrings' is true, any double quote characters that
%                           appear as part of a text variable are replaced by two
%                           double quote characters.
%
%          'DateLocale'     The locale that writecell uses to create month and
%                           day names when writing datetimes to the file. LOCALE must
%                           be a character vector or scalar string in the form xx_YY.
%                           See the documentation for DATETIME for more information.
%
%          'Encoding'       The encoding to use when creating the file.
%                           Default is 'UTF-8'.
%
%          'WriteMode'      Append to an existing file or overwrite an
%                           existing file.
%                             'overwrite' - Overwrite the file, if it
%                                           exists. This is the default option.
%                             'append'    - Append to the bottom of the file,
%                                           if it exists.
%
%   .xls, .xlsx, .xlsb, .xlsm, .xltx, .xltm:  Spreadsheet file.
%
%          WRITECELL creates a column-oriented spreadsheet file, i.e., each column
%          of each variable in C is written out as a column in the file.
%
%          Use the following optional parameter name/value pairs to control how data
%          are written to a spreadsheet file:
%
%          'DateLocale'     The locale that writecell uses to create month and day
%                           names when writing datetimes to the file. LOCALE must be
%                           a character vector or scalar string in the form xx_YY.
%                           Note: The 'DateLocale' parameter value is ignored
%                           whenever dates can be written as Excel-formatted dates.
%
%          'Sheet'          The sheet to write, specified the worksheet name, or a
%                           positive integer indicating the worksheet index.
%
%          'Range'          A character vector or scalar string that specifies a
%                           rectangular portion of the worksheet to write, using the
%                           Excel A1 reference style.
%
%          'UseExcel'      A logical value that specifies whether or not to create the
%                          spreadsheet file using Microsoft(R) Excel(R) for Windows(R). Set
%                          'UseExcel' to one of these values:
%                               false -  Does not open an instance of Microsoft Excel
%                                        to write the file. This is the default setting.
%                                        This setting may cause the data to be
%                                        written differently for files with
%                                        live updates (e.g. formula evaluation or plugins).
%                               true  -  Opens an instance of Microsoft Excel to write
%                                        the file on a Windows system with Excel installed.
%
%          'WriteMode'     Perform an in-place write, append to an existing
%                          file or sheet, overwrite an existing file or
%                          sheet.
%                             'inplace'         - In-place replacement of
%                                                 the data in the sheet.
%                                                 This is the default
%                                                 option.
%                             'overwritesheet'  - If sheet exists,
%                                                 overwrite contents of sheet.
%                             'replacefile'     - Create a new file. Prior
%                                                 contents of the file and
%                                                 all the sheets are removed.
%                             'append'          - Append to the bottom of
%                                                 the occupied range within
%                                                 the sheet.
%
%   In some cases, WRITECELL creates a file that does not represent C
%   exactly, as described below. If you use READCELL(FILENAME) to read that
%   file back in and create a new cell array, the result may not have exactly
%   the same format or contents as the original cell array.
%
%   *  WRITECELL writes out numeric data using long g format, and
%      categorical or character data as unquoted text.
%   *  WRITECELL writes out cell arrays that have more than two dimensions as two
%      dimensional cell array, with trailing dimensions collapsed.
%
%   See also READCELL, READTABLE, READMATRIX, WRITETABLE, WRITECELL.

%   Copyright 2018-2019 The MathWorks, Inc.

import matlab.io.internal.utility.suggestWriteFunctionCorrection
import matlab.io.internal.validators.validateSupportedWriteCellType
import matlab.io.internal.validators.validateWriteFunctionArgumentOrder

validateSupportedWriteCellType(C);

if nargin < 2
    cellname = inputname(1);
    if isempty(cellname)
        cellname = 'cell';
    end
    filename = [cellname '.txt'];
else
    for i = 1:2:numel(varargin)
        n = strlength(varargin{i});
        if n > 5 && strncmpi(varargin{i},'WriteVariableNames',n)
            error(message(...
                'MATLAB:table:write:WriteVariableNamesNotSupported',...
                'WRITECELL'));
        end
        if n > 5 && strncmpi(varargin{i},'WriteRowNames',n)
            error(message(...
                'MATLAB:table:write:WriteRowNamesNotSupported',...
                'WRITECELL'));
        end
    end
end

validateWriteFunctionArgumentOrder(C, filename, "writecell",...
    "cell", @iscell);

if ~iscell(C)
    suggestWriteFunctionCorrection(C, "writecell");
end

try
    T = table(C);
    writetable(T,filename,'WriteVariableNames', false,...
        'WriteRowNames', false, varargin{:});
catch ME
    throw(ME)
end

end
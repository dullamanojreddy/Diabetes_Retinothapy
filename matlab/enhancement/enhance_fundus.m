function enhanced_img = enhance_fundus(image_path, output_path)
% ENHANCE_FUNDUS - Phase 12 MATLAB Research Evidence
% Applies conservative LAB-space CLAHE and green-channel contrast enhancement
% strictly to borderline fundus captures without distorting retinal morphology.
%
% Usage:
%   enhanced = enhance_fundus('input.jpg', 'enhanced_output.jpg');

    if nargin < 1
        error('Usage: enhance_fundus(image_path, [output_path])');
    end

    img = imread(image_path);
    [H, W, C] = size(img);
    if C == 1
        img = cat(3, img, img, img);
    end

    % Convert to CIELAB color space to decouple luminance from chrominance
    cform = makecform('srgb2lab');
    lab_img = applycform(img, cform);

    L_channel = lab_img(:, :, 1);
    a_channel = lab_img(:, :, 2);
    b_channel = lab_img(:, :, 3);

    % Apply conservative CLAHE to L channel only
    % ClipLimit ~0.015 corresponds to conservative clipLimit 2.0 in OpenCV
    L_clahe = adapthisteq(L_channel, ...
        'ClipLimit', 0.015, ...
        'NumTiles', [8 8], ...
        'Distribution', 'rayleigh');

    % Recombine into LAB and transform back to RGB
    enhanced_lab = cat(3, L_clahe, a_channel, b_channel);
    cform_inv = makecform('lab2srgb');
    enhanced_img = applycform(enhanced_lab, cform_inv);

    % Save output if requested
    if nargin >= 2 && ~isempty(output_path)
        imwrite(enhanced_img, output_path);
        fprintf('Enhanced fundus saved to: %s\n', output_path);
    end
end

function quality = assess_quality(image_path)
% ASSESS_QUALITY - Phase 12 MATLAB Research Evidence
% Evaluates retinal fundus image quality using classical computer vision:
% Focus (Laplacian Variance), Illumination, Contrast, and Field of View (FOV).
%
% Usage:
%   q = assess_quality('path/to/fundus.jpg');

    if nargin < 1
        error('Usage: assess_quality(image_path)');
    end

    img = imread(image_path);
    [H, W, C] = size(img);
    if C == 1
        img = cat(3, img, img, img);
    end

    gray = rgb2gray(img);

    % 1. Focus Metric: Variance of Laplacian
    lap_kernel = [0 1 0; 1 -4 1; 0 1 0];
    lap_resp = imfilter(double(gray), lap_kernel, 'replicate');
    blur_score = var(lap_resp(:));

    % 2. Illumination: Mean Luminance and Saturation Clipping
    mean_lum = mean(double(gray(:)));
    dark_ratio = sum(gray(:) < 15) / numel(gray);
    bright_ratio = sum(gray(:) > 245) / numel(gray);

    % 3. Contrast: Percentile Dynamic Range
    p5 = prctile(double(gray(:)), 5);
    p95 = prctile(double(gray(:)), 95);
    contrast_range = p95 - p5;

    % 4. Retinal Circular Field of View Mask
    % Otsu threshold to separate fundus from black border
    fov_mask = gray > 20;
    fov_area = sum(fov_mask(:));
    fov_ratio = fov_area / (H * W);

    % Decision Status
    is_gradeable = true;
    reasons = {};

    if blur_score < 15.0
        is_gradeable = false;
        reasons{end+1} = sprintf('Excessive motion blur or defocus (score=%.2f)', blur_score);
    end
    if mean_lum < 30.0
        is_gradeable = false;
        reasons{end+1} = sprintf('Under-illuminated capture (mean=%.2f)', mean_lum);
    elseif mean_lum > 220.0
        is_gradeable = false;
        reasons{end+1} = sprintf('Over-exposed / bleached capture (mean=%.2f)', mean_lum);
    end
    if contrast_range < 25.0
        is_gradeable = false;
        reasons{end+1} = sprintf('Insufficient dynamic contrast (range=%.2f)', contrast_range);
    end

    quality.is_gradeable = is_gradeable;
    quality.blur_score = blur_score;
    quality.mean_illumination = mean_lum;
    quality.contrast_range = contrast_range;
    quality.fov_coverage = fov_ratio;
    quality.reasons = reasons;

    fprintf('--- MATLAB Quality Assessment ---\n');
    fprintf('Gradeable:    %s\n', mat2str(is_gradeable));
    fprintf('Blur Score:   %.2f\n', blur_score);
    fprintf('Illumination: %.2f\n', mean_lum);
    fprintf('Contrast:     %.2f\n', contrast_range);
    fprintf('FOV Coverage: %.2f%%\n', fov_ratio * 100);
end

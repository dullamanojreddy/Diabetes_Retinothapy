function [vessel_mask, skeleton_mask, stats] = segment_vessels(image_path)
% SEGMENT_VESSELS - Phase 12 MATLAB Research Evidence
% Classical morphological vessel tree segmentation and skeletonization on the green channel.
%
% Usage:
%   [vessels, skel, stats] = segment_vessels('fundus.jpg');

    if nargin < 1
        error('Usage: segment_vessels(image_path)');
    end

    img = imread(image_path);
    [H, W, C] = size(img);
    if C == 1
        green = img;
    else
        green = img(:, :, 2); % Green channel provides highest vascular contrast
    end

    % 1. Contrast-limited adaptive histogram equalization
    green_clahe = adapthisteq(green, 'ClipLimit', 0.02, 'NumTiles', [8 8]);

    % 2. Morphological top-hat with disc structuring element to isolate linear vessels
    se = strel('disk', 6);
    top_hat = imtophat(green_clahe, se);
    bot_hat = imbothat(green_clahe, se);
    enhanced = imsubtract(imadd(green_clahe, top_hat), bot_hat);

    % 3. Adaptive thresholding for binary vessel tree
    T = adaptthresh(enhanced, 0.45, 'NeighborhoodSize', 2*floor(size(green)/16)+1);
    vessel_raw = imbinarize(enhanced, T);

    % 4. Remove small noise components and clean boundaries
    vessel_mask = bwareaopen(vessel_raw, 25);

    % Mask out circular dark FOV border
    fov_mask = green > 15;
    vessel_mask = vessel_mask & fov_mask;

    % 5. Morphological skeletonization
    skeleton_mask = bwmorph(vessel_mask, 'skel', Inf);
    branch_points = bwmorph(skeleton_mask, 'branchpoints');

    % 6. Morphological statistics
    fov_area = sum(fov_mask(:));
    vessel_area = sum(vessel_mask(:));
    coverage = vessel_area / max(fov_area, 1);
    branch_density = sum(branch_points(:)) / max(vessel_area, 1);

    stats.vessel_coverage = coverage;
    stats.branch_density = branch_density;
    stats.num_branch_points = sum(branch_points(:));

    fprintf('--- MATLAB Vessel Segmentation ---\n');
    fprintf('Vessel Coverage: %.2f%%\n', coverage * 100);
    fprintf('Branch Density:  %.4f\n', branch_density);
    fprintf('Branch Points:   %d\n', stats.num_branch_points);
end

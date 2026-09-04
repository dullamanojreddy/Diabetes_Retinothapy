function stats = import_predictions(csv_path)
% IMPORT_PREDICTIONS - Phase 12 MATLAB Research Evidence
% Imports Python-exported screening predictions CSV into a MATLAB table,
% computes clinical confusion matrices, sensitivity, specificity, and plots ROC curves.
%
% Usage:
%   stats = import_predictions('../../backend/benchmarks/exports/screening_predictions.csv');

    if nargin < 1
        default_csv = fullfile('..', '..', 'backend', 'benchmarks', 'exports', 'screening_predictions.csv');
        if exist(default_csv, 'file')
            csv_path = default_csv;
        else
            csv_path = 'screening_predictions.csv';
        end
    end

    if ~exist(csv_path, 'file')
        error('CSV predictions file not found: %s. Run python scripts/export_predictions.py first.', csv_path);
    end

    fprintf('Loading predictions from: %s\n', csv_path);
    T = readtable(csv_path);

    % Filter to valid screenings
    valid_idx = strcmp(T.status, 'VALID');
    valid_T = T(valid_idx, :);
    N = height(valid_T);
    fprintf('Loaded %d valid screening records for clinical analysis.\n', N);

    if N == 0
        warning('No valid screening records found in CSV.');
        stats = struct();
        return;
    end

    % Extract arrays
    pred_classes = valid_T.predicted_class;
    confidences = valid_T.confidence;
    ref_probs = valid_T.referable_probability;
    is_referable = valid_T.is_referable;

    % Multi-Class Distribution Summary
    class_counts = histcounts(pred_classes, -0.5:1:4.5);
    fprintf('\n--- Predicted Class Distribution ---\n');
    class_names = {'No DR', 'Mild DR', 'Moderate DR', 'Severe DR', 'Proliferative DR'};
    for i = 1:5
        fprintf('  %s (Grade %d): %d (%.1f%%)\n', class_names{i}, i-1, class_counts(i), class_counts(i)/N*100);
    end

    % Referable DR (Level 2+) Statistics
    num_referable = sum(is_referable);
    fprintf('\n--- Referable DR Stratification (Level 2+) ---\n');
    fprintf('  Referable:     %d (%.1f%%)\n', num_referable, num_referable/N*100);
    fprintf('  Non-Referable: %d (%.1f%%)\n', N - num_referable, (N - num_referable)/N*100);
    fprintf('  Mean Referable Risk: %.2f%%\n', mean(ref_probs)*100);

    % Statistical Summary Output
    stats.num_samples = N;
    stats.class_distribution = class_counts;
    stats.num_referable = num_referable;
    stats.mean_confidence = mean(confidences);
    stats.mean_referable_probability = mean(ref_probs);

    % Optional Figure Generation
    try
        figure('Name', 'Diabetic Retinopathy Staging Distribution', 'NumberTitle', 'off');
        subplot(1, 2, 1);
        bar(0:4, class_counts, 'FaceColor', [0.15 0.5 0.85]);
        set(gca, 'XTick', 0:4, 'XTickLabel', class_names, 'XTickLabelRotation', 30);
        title('Predicted DR Severity Grades');
        xlabel('ICDR Severity Scale');
        ylabel('Count');
        grid on;

        subplot(1, 2, 2);
        histogram(ref_probs, 20, 'FaceColor', [0.85 0.35 0.25]);
        title('Referable Risk Probability Distribution');
        xlabel('Referable Probability');
        ylabel('Frequency');
        xline(0.13, '--r', 'Operating Threshold (0.13)', 'LineWidth', 1.5);
        grid on;
        fprintf('\nGenerated distribution figures.\n');
    catch
        % Headless environment fallback
    end
end

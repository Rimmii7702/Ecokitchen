document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const dropArea = document.getElementById('heatmapDropArea');
    const fileInput = document.getElementById('heatmapFileInput');
    const previewImage = document.getElementById('heatmapPreviewImage');
    const uploadForm = document.getElementById('heatmapUploadForm');
    const loadingSpinner = document.getElementById('heatmapLoadingSpinner');
    const resultsContainer = document.getElementById('heatmapResultsContainer');
    const newAnalysisBtn = document.getElementById('newHeatmapAnalysisBtn');
    const uploadBtn = document.getElementById('heatmapUploadBtn');

    // Click on upload area to trigger file input
    if (dropArea) {
        dropArea.addEventListener('click', function() {
            fileInput.click();
        });

        // Handle drag and drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });

        // Handle dropped files
        dropArea.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;

            if (files.length) {
                fileInput.files = files;
                updatePreview(files[0]);
            }
        });
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        dropArea.classList.add('highlight');
    }

    function unhighlight() {
        dropArea.classList.remove('highlight');
    }

    // Handle file selection
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length) {
                updatePreview(fileInput.files[0]);
            }
        });
    }

    // Update image preview
    function updatePreview(file) {
        if (file) {
            const reader = new FileReader();

            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewImage.style.display = 'block';
            };

            reader.readAsDataURL(file);
        }
    }

    // Form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            if (!fileInput.files.length) {
                e.preventDefault();
                alert('Please select an image first.');
                return;
            }

            loadingSpinner.style.display = 'block';
        });
    }

    // New analysis button
    if (newAnalysisBtn) {
        newAnalysisBtn.addEventListener('click', function() {
            resultsContainer.style.display = 'none';
            previewImage.style.display = 'none';
            fileInput.value = '';
            uploadForm.reset();
        });
    }

    // Check if results should be displayed
    if (resultsContainer && document.getElementById('wasteAreasTable').children.length > 0) {
        resultsContainer.style.display = 'block';
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
    }
});
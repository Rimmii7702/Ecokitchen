document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const staticBtn = document.getElementById('static-btn');
    const videoBtn = document.getElementById('video-btn');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const videoForm = document.getElementById('video-form');
    const videoLoading = document.getElementById('video-loading');
    const videoError = document.getElementById('video-error');

    staticBtn.addEventListener('click', () => {
        uploadForm.classList.remove('hidden');
        videoForm.classList.add('hidden');
    });

    videoBtn.addEventListener('click', () => {
        uploadForm.classList.add('hidden');
        videoForm.classList.remove('hidden');
    });

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        loading.classList.remove('hidden');
        error.classList.add('hidden');
        error.textContent = '';

        const formData = new FormData(uploadForm);

        try {
            console.log('Submitting form data');
            const response = await fetch('/upload_image', {
                method: 'POST',
                body: formData
            });

            console.log('Response status:', response.status);
            if (response.redirected) {
                console.log('Redirecting to:', response.url);
                window.location.href = response.url;
                return;
            }

            const result = await response.json();
            console.log('Response JSON:', result);
            if (result.error) {
                throw new Error(result.error);
            }
        } catch (err) {
            console.error('Error:', err);
            error.textContent = err.message;
            error.classList.remove('hidden');
        } finally {
            loading.classList.add('hidden');
        }
    });

    videoForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        videoLoading.classList.remove('hidden');
        videoError.classList.add('hidden');
        videoError.textContent = '';

        const formData = new FormData(videoForm);

        try {
            console.log('Submitting video data');
            const response = await fetch('/upload_video', {
                method: 'POST',
                body: formData
            });

            console.log('Response status:', response.status);
            if (response.redirected) {
                console.log('Redirecting to:', response.url);
                window.location.href = response.url;
                return;
            }

            const result = await response.json();
            console.log('Response JSON:', result);
            if (result.error) {
                throw new Error(result.error);
            }
        } catch (err) {
            console.error('Error:', err);
            videoError.textContent = err.message;
            videoError.classList.remove('hidden');
        } finally {
            videoLoading.classList.add('hidden');
        }
    });
});
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const urlInput = document.getElementById('videoUrl');
    const pasteBtn = document.getElementById('pasteBtn');
    const qualityOptions = document.getElementById('qualityOptions');
    const formatOptions = document.getElementById('formatOptions');
    const downloadBtn = document.getElementById('downloadBtn');
    const progressCircle = document.querySelector('.progress-ring-circle');
    const progressText = document.getElementById('progressText');
    const progressStatus = document.getElementById('progressStatus');
    const progressBar = document.getElementById('progressBar');

    // State
    let selectedQuality = '1080p';
    let selectedFormat = 'mp4';
    let isDownloading = false;

    // Paste button
    pasteBtn.addEventListener('click', async function() {
        if (navigator.clipboard) {
            const text = await navigator.clipboard.readText();
            urlInput.value = text;
        }
    });

    // Quality selection
    qualityOptions.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', function() {
            qualityOptions.querySelectorAll('button').forEach(b => b.classList.remove('ring', 'ring-2', 'ring-neon-purple'));
            this.classList.add('ring', 'ring-2', 'ring-neon-purple');
            selectedQuality = this.getAttribute('data-quality');
        });
    });
    // Default select first
    qualityOptions.querySelector('button').classList.add('ring', 'ring-2', 'ring-neon-purple');

    // Format selection
    formatOptions.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', function() {
            formatOptions.querySelectorAll('button').forEach(b => b.classList.remove('ring', 'ring-2', 'ring-neon-pink'));
            this.classList.add('ring', 'ring-2', 'ring-neon-pink');
            selectedFormat = this.getAttribute('data-format');
        });
    });
    // Default select first
    formatOptions.querySelector('button').classList.add('ring', 'ring-2', 'ring-neon-pink');

    // Download button
    downloadBtn.addEventListener('click', async function() {
        if (isDownloading) return;
        const url = urlInput.value.trim();
        if (!url) {
            urlInput.classList.add('border-red-500');
            urlInput.focus();
            return;
        }
        urlInput.classList.remove('border-red-500');
        isDownloading = true;
        downloadBtn.disabled = true;
        progressStatus.textContent = 'Starting...';
        progressText.textContent = '0%';
        progressBar.style.width = '0%';
        progressCircle.style.strokeDashoffset = 251;

        // POST to backend
        try {
            progressStatus.textContent = 'Requesting download...';
            const res = await fetch('/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, quality: selectedQuality, format: selectedFormat })
            });
            const data = await res.json();
            let percent = 100;
            if (data.success) {
                progressStatus.textContent = 'Download complete!';
                progressText.textContent = '100%';
                progressBar.style.width = '100%';
                progressCircle.style.strokeDashoffset = 0;
            } else {
                progressStatus.textContent = 'Failed';
                progressText.textContent = '0%';
                progressBar.style.width = '0%';
                progressCircle.style.strokeDashoffset = 251;
            }
        } catch (e) {
            progressStatus.textContent = 'Error';
            progressText.textContent = '0%';
            progressBar.style.width = '0%';
            progressCircle.style.strokeDashoffset = 251;
        }
        isDownloading = false;
        downloadBtn.disabled = false;
    });
}); 
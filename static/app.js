const form = document.getElementById('downloadForm');
const statusDiv = document.getElementById('status');
const loader = document.getElementById('loader');
const downloadBtn = document.getElementById('downloadBtn');

form.addEventListener('submit', function(e) {
    e.preventDefault();

    statusDiv.style.display = 'none';
    loader.style.display = 'block';
    downloadBtn.disabled = true;
    downloadBtn.textContent = 'Downloading...';

    const url = document.getElementById('videoUrl').value.trim();
    const removeWatermark = document.getElementById('removeWatermark').checked;

    fetch('/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, removeWatermark })
    })
    .then(res => res.json())
    .then(data => {
        loader.style.display = 'none';
        downloadBtn.disabled = false;
        downloadBtn.textContent = 'Download Video';
        statusDiv.style.display = 'block';

        if (data.success) {
            statusDiv.className = 'status success';
            let html = '✅ ' + data.message;
            if (data.file_url) {
                html += `<br><a href="${data.file_url}" class="download-link" download>⬇️ Download File (${data.filename ? data.filename : ''}${data.size ? ' - ' + (data.size/1048576).toFixed(1) + ' MB' : ''})</a>`;
            }
            statusDiv.innerHTML = html;
        } else {
            statusDiv.className = 'status error';
            statusDiv.textContent = '❌ ' + data.message;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        loader.style.display = 'none';
        downloadBtn.disabled = false;
        downloadBtn.textContent = 'Download Video';
        statusDiv.style.display = 'block';
        statusDiv.className = 'status error';
        statusDiv.textContent = '❌ DazzloGet: An error occurred. Please try again.';
    });
}); 
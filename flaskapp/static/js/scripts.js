document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('uploadForm');
    const notification = document.getElementById('notification');

    // Trigger file input when drop zone is clicked
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop handling
    dropZone.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropZone.style.backgroundColor = '#e9ecef';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.backgroundColor = '#f9f9f9';
    });

    dropZone.addEventListener('drop', (event) => {
        event.preventDefault();
        dropZone.style.backgroundColor = '#f9f9f9';
        fileInput.files = event.dataTransfer.files;
    });

    // Show notification
    function showNotification(message) {
        notification.textContent = message;
        notification.classList.add('show');
        setTimeout(() => {
            notification.classList.remove('show');
        }, 2000); // Hide after 2 seconds
    }

    // Show notification if there's a Flask message
    if (document.querySelector('ul li')) {
        showNotification('Files successfully uploaded and processed!');
    }
});

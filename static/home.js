// home.js - JavaScript for index.html (Upload page)
// This file handles image upload, drag-and-drop, file processing, and canvas editing

(function () {
  "use strict";

  // DOM Elements
  let dropZone, fileInput, filePreview, fileList, processBtn, loading;
  let resultsSection, resultsContainer;
  let canvasModal, drawCanvas, objectsList;
  let selectedFiles = [];
  let currentCanvasData = null;

  // Initialize on DOM ready
  document.addEventListener("DOMContentLoaded", function () {
    initElements();
    initEventListeners();
  });

  function initElements() {
    dropZone = document.getElementById("dropZone");
    fileInput = document.getElementById("fileInput");
    filePreview = document.getElementById("filePreview");
    fileList = document.getElementById("fileList");
    processBtn = document.getElementById("processBtn");
    loading = document.getElementById("loading");
    resultsSection = document.getElementById("resultsSection");
    resultsContainer = document.getElementById("resultsContainer");
    canvasModal = document.getElementById("canvasModal");
    drawCanvas = document.getElementById("drawCanvas");
    objectsList = document.getElementById("objectsList");
  }

  function initEventListeners() {
    // File input change
    if (fileInput) {
      fileInput.addEventListener("change", handleFileSelect);
    }

    // Drag and drop events
    if (dropZone) {
      dropZone.addEventListener("click", () => fileInput?.click());
      dropZone.addEventListener("dragover", handleDragOver);
      dropZone.addEventListener("dragleave", handleDragLeave);
      dropZone.addEventListener("drop", handleDrop);
    }

    // Process button
    if (processBtn) {
      processBtn.addEventListener("click", processImages);
    }
  }

  function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      selectedFiles = files;
      displayFilePreview();
    }
  }

  function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add("drag-over");
  }

  function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove("drag-over");
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove("drag-over");

    const files = Array.from(e.dataTransfer.files).filter((file) =>
      file.type.startsWith("image/")
    );

    if (files.length > 0) {
      selectedFiles = files;
      fileInput.files = e.dataTransfer.files;
      displayFilePreview();
    }
  }

  function displayFilePreview() {
    fileList.innerHTML = "";
    selectedFiles.forEach((file, index) => {
      const fileItem = document.createElement("div");
      fileItem.className =
        "flex items-center justify-between bg-gray-50 p-3 rounded";
      fileItem.innerHTML = `
                <div class="flex items-center">
                    <svg class="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    <span class="text-sm text-gray-700">${file.name}</span>
                    <span class="text-xs text-gray-500 ml-2">(${formatFileSize(
                      file.size
                    )})</span>
                </div>
                <button onclick="window.HomeApp.removeFile(${index})" class="text-red-500 hover:text-red-700">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            `;
      fileList.appendChild(fileItem);
    });
    filePreview.classList.remove("hidden");
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  }

  function removeFile(index) {
    selectedFiles.splice(index, 1);
    if (selectedFiles.length === 0) {
      filePreview.classList.add("hidden");
      fileInput.value = "";
    } else {
      displayFilePreview();
    }
  }

  async function processImages() {
    if (selectedFiles.length === 0) return;

    loading.classList.remove("hidden");
    processBtn.disabled = true;
    resultsContainer.innerHTML = "";
    resultsSection.classList.add("hidden");

    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const response = await fetch("/api/segment", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Processing failed");
      }

      const results = await response.json();
      displayResults(results);
    } catch (error) {
      console.error("Error processing images:", error);
      alert("Failed to process images. Please try again.");
    } finally {
      loading.classList.add("hidden");
      processBtn.disabled = false;
    }
  }

  function displayResults(results) {
    resultsContainer.innerHTML = "";

    results.forEach((result) => {
      const resultCard = createResultCard(result);
      resultsContainer.appendChild(resultCard);
    });

    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth" });
  }

  function createResultCard(result) {
    const card = document.createElement("div");
    card.className = "bg-gray-50 rounded-lg overflow-hidden";

    const objectsDetected = result.objects?.length || 0;
    const classes = result.objects
      ? [...new Set(result.objects.map((obj) => obj.class_name))]
      : [];

    card.innerHTML = `
            <img src="${
              result.image_url
            }" alt="Segmented image" class="w-full h-64 object-cover">
            <div class="p-4">
                <div class="flex justify-between items-center mb-3">
                    <span class="text-sm font-semibold text-gray-900">${objectsDetected} objects detected</span>
                    <span class="text-xs text-gray-500">${
                      result.filename
                    }</span>
                </div>
                <div class="flex flex-wrap gap-1 mb-4">
                    ${classes
                      .map(
                        (cls) => `
                        <span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                            ${cls}
                        </span>
                    `
                      )
                      .join("")}
                </div>
                <div class="flex space-x-2">
                    <button onclick="window.HomeApp.openCanvasEditor('${
                      result.file_id
                    }')" 
                            class="flex-1 bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition text-sm font-medium">
                        Edit in Canvas
                    </button>
                    <a href="${result.image_url}" download 
                       class="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition text-sm font-medium text-center">
                        Download
                    </a>
                </div>
            </div>
        `;

    return card;
  }

  async function openCanvasEditor(fileId) {
    try {
      const response = await fetch(`/api/details/${fileId}`);
      if (!response.ok) throw new Error("Failed to fetch details");

      const data = await response.json();
      currentCanvasData = data;

      initCanvas(data);
      canvasModal.classList.remove("hidden");
      canvasModal.classList.add("flex");
    } catch (error) {
      console.error("Error opening canvas:", error);
      alert("Failed to load canvas data");
    }
  }

  function initCanvas(data) {
    const ctx = drawCanvas.getContext("2d");
    const img = new Image();

    img.onload = function () {
      drawCanvas.width = img.width;
      drawCanvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      // Draw detection boxes and masks
      if (data.objects) {
        data.objects.forEach((obj, index) => {
          drawObject(ctx, obj, index);
        });
        displayObjectsList(data.objects);
      }
    };

    img.src = data.image_url;
  }

  function drawObject(ctx, obj, index) {
    const colors = [
      "#FF6B6B",
      "#4ECDC4",
      "#45B7D1",
      "#FFA07A",
      "#98D8C8",
      "#F7DC6F",
      "#BB8FCE",
      "#85C1E2",
      "#F8B739",
      "#52B788",
    ];
    const color = colors[index % colors.length];

    // Draw bounding box if available
    if (obj.bbox) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.strokeRect(obj.bbox[0], obj.bbox[1], obj.bbox[2], obj.bbox[3]);

      // Draw label
      ctx.fillStyle = color;
      ctx.fillRect(obj.bbox[0], obj.bbox[1] - 25, 150, 25);
      ctx.fillStyle = "#FFFFFF";
      ctx.font = "bold 14px Arial";
      ctx.fillText(
        `${obj.class_name} (${(obj.confidence * 100).toFixed(1)}%)`,
        obj.bbox[0] + 5,
        obj.bbox[1] - 7
      );
    }
  }

  function displayObjectsList(objects) {
    objectsList.innerHTML = "";
    objects.forEach((obj, index) => {
      const item = document.createElement("div");
      item.className = "p-2 bg-white rounded text-sm";
      item.innerHTML = `
                <div class="font-semibold">${obj.class_name}</div>
                <div class="text-xs text-gray-500">Confidence: ${(
                  obj.confidence * 100
                ).toFixed(1)}%</div>
            `;
      objectsList.appendChild(item);
    });
  }

  function closeCanvasModal() {
    canvasModal.classList.add("hidden");
    canvasModal.classList.remove("flex");
    currentCanvasData = null;
  }

  function downloadCanvas() {
    const link = document.createElement("a");
    link.download = "segmented-canvas.png";
    link.href = drawCanvas.toDataURL();
    link.click();
  }

  // Expose public API
  window.HomeApp = {
    removeFile,
    openCanvasEditor,
    closeCanvasModal,
    downloadCanvas,
  };

  // Make functions globally accessible for inline onclick handlers
  window.closeCanvasModal = closeCanvasModal;
  window.downloadCanvas = downloadCanvas;
})();

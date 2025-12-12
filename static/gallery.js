// gallery.js - JavaScript for gallery.html (Gallery page)
// This file handles image gallery display, modals, image details, deletion, and canvas editing

(function () {
  "use strict";

  // DOM Elements
  let imageModal, modalImage;
  let canvasModal, drawCanvas, canvasObjectsList;
  let currentCanvasData = null;

  // Initialize on DOM ready
  document.addEventListener("DOMContentLoaded", function () {
    initElements();
    initEventListeners();
  });

  function initElements() {
    imageModal = document.getElementById("imageModal");
    modalImage = document.getElementById("modalImage");
    canvasModal = document.getElementById("canvasModal");
    drawCanvas = document.getElementById("drawCanvas");
    canvasObjectsList = document.getElementById("canvasObjectsList");
  }

  function initEventListeners() {
    // Close modal on background click
    if (imageModal) {
      imageModal.addEventListener("click", function (e) {
        if (e.target === imageModal) {
          closeModal();
        }
      });
    }

    if (canvasModal) {
      canvasModal.addEventListener("click", function (e) {
        if (e.target === canvasModal) {
          closeCanvasModal();
        }
      });
    }

    // Keyboard shortcuts
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        closeModal();
        closeCanvasModal();
      }
    });
  }

  // Image Modal Functions
  function openModal(imageUrl) {
    if (modalImage && imageModal) {
      modalImage.src = imageUrl;
      imageModal.classList.add("active");
    }
  }

  function closeModal() {
    if (imageModal) {
      imageModal.classList.remove("active");
      if (modalImage) {
        modalImage.src = "";
      }
    }
  }

  // Delete Image Function
  async function deleteImage(fileId) {
    if (!confirm("Are you sure you want to delete this image?")) {
      return;
    }

    try {
      const response = await fetch(`/api/delete/${fileId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete image");
      }

      // Reload page to show updated gallery
      window.location.reload();
    } catch (error) {
      console.error("Error deleting image:", error);
      alert("Failed to delete image. Please try again.");
    }
  }

  // Canvas Drawing Functions
  async function drawWithCanvas(fileId) {
    try {
      const response = await fetch(`/api/details/${fileId}`);
      if (!response.ok) {
        throw new Error("Failed to fetch details");
      }

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
        displayCanvasObjectsList(data.objects);
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

      // Draw label background
      ctx.fillStyle = color;
      ctx.fillRect(obj.bbox[0], obj.bbox[1] - 25, 150, 25);

      // Draw label text
      ctx.fillStyle = "#FFFFFF";
      ctx.font = "bold 14px Arial";
      ctx.fillText(
        `${obj.class_name} (${(obj.confidence * 100).toFixed(1)}%)`,
        obj.bbox[0] + 5,
        obj.bbox[1] - 7
      );
    }
  }

  function displayCanvasObjectsList(objects) {
    if (!canvasObjectsList) return;

    canvasObjectsList.innerHTML = "";
    objects.forEach((obj, index) => {
      const item = document.createElement("div");
      item.className = "p-2 bg-white rounded text-sm";
      item.innerHTML = `
                <div class="font-semibold">${obj.class_name}</div>
                <div class="text-xs text-gray-500">Confidence: ${(
                  obj.confidence * 100
                ).toFixed(1)}%</div>
            `;
      canvasObjectsList.appendChild(item);
    });
  }

  function closeCanvasModal() {
    if (canvasModal) {
      canvasModal.classList.add("hidden");
      canvasModal.classList.remove("flex");
      currentCanvasData = null;
    }
  }

  function downloadCanvas() {
    if (!drawCanvas) return;

    const link = document.createElement("a");
    link.download = `segmented-canvas-${Date.now()}.png`;
    link.href = drawCanvas.toDataURL("image/png");
    link.click();
  }

  // Expose public API
  window.GalleryApp = {
    openModal,
    closeModal,
    deleteImage,
    drawWithCanvas,
    closeCanvasModal,
    downloadCanvas,
  };

  // Make functions globally accessible for inline onclick handlers
  window.openModal = openModal;
  window.closeModal = closeModal;
  window.deleteImage = deleteImage;
  window.drawWithCanvas = drawWithCanvas;
  window.closeCanvasModal = closeCanvasModal;
  window.downloadCanvas = downloadCanvas;
})();

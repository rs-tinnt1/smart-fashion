// product-detail.js - Client-side mask rendering for product detail page

(function () {
  "use strict";

  // Color mapping for clothing tags
  const TAG_COLORS = {
    "short sleeve top": "#FF6B6B", // Red
    "long sleeve top": "#4ECDC4", // Teal
    "short sleeve outwear": "#45B7D1", // Blue
    "long sleeve outwear": "#96CEB4", // Green
    vest: "#FFEAA7", // Yellow
    sling: "#DFE6E9", // Light Gray
    shorts: "#74B9FF", // Light Blue
    trousers: "#A29BFE", // Purple
    skirt: "#FD79A8", // Pink
    "short sleeve dress": "#FDCB6E", // Orange
    "long sleeve dress": "#6C5CE7", // Indigo
    "vest dress": "#00B894", // Emerald
    "sling dress": "#E17055", // Coral
  };

  let canvas, ctx, originalImage;
  let detectionsData = [];
  let fileId = "";
  let originalUrl = "";

  // Initialize on DOM ready
  document.addEventListener("DOMContentLoaded", function () {
    initCanvas();
    setupEventListeners();
  });

  function initCanvas() {
    canvas = document.getElementById("productCanvas");
    if (!canvas) return;

    ctx = canvas.getContext("2d");
    originalImage = document.getElementById("originalImage");

    // Get data from template
    const detectionsJson = document.getElementById("detectionsData");
    if (detectionsJson) {
      detectionsData = JSON.parse(detectionsJson.textContent);
    }

    fileId = document.getElementById("fileId")?.textContent || "";
    originalUrl = document.getElementById("originalUrl")?.textContent || "";

    // Load and draw image
    originalImage.onload = function () {
      canvas.width = originalImage.naturalWidth;
      canvas.height = originalImage.naturalHeight;
      drawCanvas();
    };

    // Trigger load if image is already cached
    if (originalImage.complete) {
      originalImage.onload();
    }
  }

  function setupEventListeners() {
    // Toggle mask checkbox
    const toggleMask = document.getElementById("toggleMask");
    if (toggleMask) {
      toggleMask.addEventListener("change", function () {
        drawCanvas();
      });
    }

    // Download button
    const downloadBtn = document.getElementById("downloadBtn");
    if (downloadBtn) {
      downloadBtn.addEventListener("click", downloadImage);
    }
  }

  function drawCanvas() {
    if (!ctx || !originalImage) return;

    const showMask = document.getElementById("toggleMask")?.checked ?? true;

    // Clear canvas and draw original image
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(originalImage, 0, 0);

    // Draw masks if enabled
    if (showMask && detectionsData.length > 0) {
      detectionsData.forEach((detection) => {
        drawDetectionMask(detection);
      });
    }
  }

  function drawDetectionMask(detection) {
    if (!detection.polygon || !detection.polygon.points_json) return;

    const color = TAG_COLORS[detection.label] || "#999999";
    let points;

    // Parse points_json if it's a string
    if (typeof detection.polygon.points_json === "string") {
      try {
        points = JSON.parse(detection.polygon.points_json);
      } catch (e) {
        console.error("Error parsing polygon points:", e);
        return;
      }
    } else {
      points = detection.polygon.points_json;
    }

    // Draw each contour
    if (Array.isArray(points)) {
      points.forEach((contour) => {
        drawPolygon(contour, color);
      });
    }
  }

  function drawPolygon(contour, color) {
    if (!contour || contour.length === 0) return;

    // Set fill style with transparency
    ctx.fillStyle = color + "80"; // 50% transparency
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;

    ctx.beginPath();
    ctx.moveTo(contour[0].x, contour[0].y);

    for (let i = 1; i < contour.length; i++) {
      ctx.lineTo(contour[i].x, contour[i].y);
    }

    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }

  function downloadImage() {
    const showMask = document.getElementById("toggleMask")?.checked ?? true;

    if (showMask) {
      // Download canvas with mask as PNG
      const link = document.createElement("a");
      link.download = `product-${fileId}-with-mask.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    } else {
      // Download original image
      const link = document.createElement("a");
      link.download = `product-${fileId}-original.jpg`;
      link.href = originalUrl;
      link.click();
    }
  }

  // Expose for debugging
  window.ProductDetail = {
    drawCanvas,
    TAG_COLORS,
  };
})();

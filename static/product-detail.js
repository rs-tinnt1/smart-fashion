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
    // Display mode radio buttons
    const radioButtons = document.querySelectorAll('input[name="displayMode"]');
    radioButtons.forEach((radio) => {
      radio.addEventListener("change", function () {
        drawCanvas();
      });
    });

    // Download button
    const downloadBtn = document.getElementById("downloadBtn");
    if (downloadBtn) {
      downloadBtn.addEventListener("click", downloadImage);
    }
  }

  function getDisplayMode() {
    const selected = document.querySelector('input[name="displayMode"]:checked');
    return selected ? selected.value : "polygon";
  }

  function drawCanvas() {
    if (!ctx || !originalImage) return;

    const displayMode = getDisplayMode();

    // Clear canvas and draw original image
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(originalImage, 0, 0);

    // Draw overlays based on mode
    if (displayMode !== "image" && detectionsData.length > 0) {
      detectionsData.forEach((detection) => {
        if (displayMode === "polygon") {
          drawDetectionPolygon(detection);
        } else if (displayMode === "rectangle") {
          drawDetectionRectangle(detection);
        }
      });
    }
  }

  function drawDetectionPolygon(detection) {
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

    // Draw label
    drawLabel(detection, color);
  }

  function drawDetectionRectangle(detection) {
    // Use bbox data from detection
    const bbox = detection.bbox;
    if (!bbox) return;

    const color = TAG_COLORS[detection.label] || "#999999";
    const { x, y, w, h } = bbox;

    // Set fill style with transparency
    ctx.fillStyle = color + "40"; // 25% transparency for rectangle
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;

    // Draw filled rectangle
    ctx.fillRect(x, y, w, h);

    // Draw border
    ctx.strokeRect(x, y, w, h);

    // Draw label at top of rectangle
    drawLabelAtPosition(detection.label, detection.confidence, x, y, color);
  }

  function drawPolygon(contour, color) {
    if (!contour || contour.length === 0) return;

    // Set fill style with transparency
    ctx.fillStyle = color + "60"; // 38% transparency
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

  function drawLabel(detection, color) {
    if (!detection.polygon || !detection.polygon.points_json) return;

    let points;
    if (typeof detection.polygon.points_json === "string") {
      try {
        points = JSON.parse(detection.polygon.points_json);
      } catch (e) {
        return;
      }
    } else {
      points = detection.polygon.points_json;
    }

    // Find top-left point from first contour
    if (points && points.length > 0 && points[0].length > 0) {
      const firstContour = points[0];
      let minY = Infinity;
      let labelX = 0;
      let labelY = 0;

      firstContour.forEach((point) => {
        if (point.y < minY) {
          minY = point.y;
          labelX = point.x;
          labelY = point.y;
        }
      });

      drawLabelAtPosition(detection.label, detection.confidence, labelX, labelY, color);
    }
  }

  function drawLabelAtPosition(label, confidence, x, y, color) {
    const text = `${label} ${(confidence * 100).toFixed(0)}%`;
    
    ctx.font = "bold 14px Arial";
    const textMetrics = ctx.measureText(text);
    const textWidth = textMetrics.width;
    const textHeight = 18;
    const padding = 4;

    // Adjust position to stay within canvas
    const labelX = Math.max(0, Math.min(x, canvas.width - textWidth - padding * 2));
    const labelY = Math.max(textHeight + padding * 2, y - 5);

    // Draw background
    ctx.fillStyle = color;
    ctx.fillRect(
      labelX,
      labelY - textHeight - padding,
      textWidth + padding * 2,
      textHeight + padding
    );

    // Draw text
    ctx.fillStyle = "#FFFFFF";
    ctx.fillText(text, labelX + padding, labelY - padding - 2);
  }

  function downloadImage() {
    const displayMode = getDisplayMode();

    if (displayMode !== "image") {
      // Download canvas with overlay as PNG
      const link = document.createElement("a");
      link.download = `product-${fileId}-${displayMode}.png`;
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
    getDisplayMode,
    TAG_COLORS,
  };
})();

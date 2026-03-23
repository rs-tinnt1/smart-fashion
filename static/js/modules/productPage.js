// productPage.js - Product detail page initialization

import { ProductCanvas } from "./productCanvas.js";

/**
 * Initialize product detail page
 */
export function initProductPage() {
  const canvas = document.getElementById("productCanvas");
  const originalImage = document.getElementById("originalImage");
  const detectionsDataEl = document.getElementById("detectionsData");
  const detectedItemsGrid = document.getElementById("detectedItemsGrid");
  const fileIdEl = document.getElementById("fileId");
  const originalUrlEl = document.getElementById("originalUrl");
  const downloadBtn = document.getElementById("downloadBtn");

  if (!canvas || !originalImage || !detectionsDataEl) return;

  // Parse data from template
  let detectionsData = [];
  try {
    detectionsData = JSON.parse(detectionsDataEl.textContent);
  } catch (e) {
    console.error("Error parsing detections data:", e);
    return;
  }

  const fileId = fileIdEl?.textContent || "";
  const originalUrl = originalUrlEl?.textContent || "";

  // Create product canvas instance
  const productCanvas = new ProductCanvas(canvas, detectionsData);

  // Load image and draw
  originalImage.onload = function () {
    productCanvas
      .loadImage(originalUrl)
      .then(() => {
        productCanvas.redraw();
        if (detectedItemsGrid && detectedItemsGrid.children.length === 0) {
          renderDetectedItems(detectedItemsGrid, originalImage, detectionsData, productCanvas);
        }
      })
      .catch((err) => {
        console.error("Error loading image:", err);
      });
  };

  // Trigger load if image is already cached
  if (originalImage.complete) {
    originalImage.onload();
  }

  // Setup display mode radio buttons
  setupDisplayModeControls(productCanvas);

  // Setup download button
  setupDownloadButton(downloadBtn, productCanvas, fileId, originalUrl);
}

function renderDetectedItems(container, sourceImage, detections, productCanvas) {
  if (!container) return;

  container.innerHTML = "";

  if (!detections.length) {
    container.innerHTML = '<p class="text-fog">No items detected</p>';
    return;
  }

  const groupedDetections = detections.reduce((acc, detection, index) => {
    const label = detection.label || "unknown";
    if (!acc[label]) {
      acc[label] = [];
    }
    acc[label].push({ detection, index });
    return acc;
  }, {});

  Object.entries(groupedDetections).forEach(([label, items]) => {
    const group = document.createElement("article");
    group.className = "rounded-2xl border border-light bg-warm-white p-4 space-y-4 fade-in-up";

    const previews = items
      .map(({ detection, index }) => {
        const color = productCanvas.getDetectionColor(detection, index);
        const confidence = `${Math.round((detection.confidence || 0) * 100)}%`;
        let cropDataUrl = "";

        try {
          cropDataUrl = createPolygonCrop(sourceImage, detection, color);
        } catch (error) {
          console.error("Failed to create polygon crop:", error);
        }

        return `
          <div class="space-y-2">
            <div class="flex items-center justify-between gap-2">
              <div class="flex items-center gap-2 min-w-0">
                <span class="w-3 h-3 rounded-full shrink-0" style="background:${color}"></span>
                <span class="text-xs font-medium text-charcoal">${confidence}</span>
              </div>
            </div>
            <div class="rounded-xl overflow-hidden border border-light bg-white aspect-[4/3] flex items-center justify-center">
              ${cropDataUrl ? `<img src="${cropDataUrl}" alt="${label}" class="w-full h-full object-contain">` : '<p class="text-xs text-fog px-4 text-center">Polygon crop unavailable</p>'}
            </div>
          </div>
        `;
      })
      .join("");

    group.innerHTML = `
      <div>
        <p class="text-sm font-semibold text-charcoal capitalize">${label}</p>
        <p class="text-xs text-fog mt-1">${items.length} detected item${items.length > 1 ? "s" : ""}</p>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">${previews}</div>
    `;

    container.appendChild(group);
  });
}

function createPolygonCrop(sourceImage, detection, color) {
  const contours = getContours(detection);
  if (!contours.length) {
    return createRectangleCrop(sourceImage, detection.bbox, color);
  }

  const bounds = getBoundsFromContours(contours);
  if (!bounds) return "";

  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, bounds.w);
  canvas.height = Math.max(1, bounds.h);
  const ctx = canvas.getContext("2d");

  if (!ctx) return "";

  ctx.save();
  ctx.beginPath();
  contours.forEach((contour) => {
    if (!contour.length) return;
    ctx.moveTo(contour[0].x - bounds.x, contour[0].y - bounds.y);
    for (let i = 1; i < contour.length; i += 1) {
      ctx.lineTo(contour[i].x - bounds.x, contour[i].y - bounds.y);
    }
    ctx.closePath();
  });
  ctx.clip();
  ctx.drawImage(sourceImage, -bounds.x, -bounds.y);
  ctx.restore();

  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  contours.forEach((contour) => {
    if (!contour.length) return;
    ctx.beginPath();
    ctx.moveTo(contour[0].x - bounds.x, contour[0].y - bounds.y);
    for (let i = 1; i < contour.length; i += 1) {
      ctx.lineTo(contour[i].x - bounds.x, contour[i].y - bounds.y);
    }
    ctx.closePath();
    ctx.stroke();
  });

  return canvas.toDataURL("image/png");
}

function createRectangleCrop(sourceImage, bbox, color) {
  if (!bbox) return "";
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, bbox.w);
  canvas.height = Math.max(1, bbox.h);
  const ctx = canvas.getContext("2d");

  if (!ctx) return "";

  ctx.drawImage(sourceImage, bbox.x, bbox.y, bbox.w, bbox.h, 0, 0, bbox.w, bbox.h);
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.strokeRect(1, 1, Math.max(0, bbox.w - 2), Math.max(0, bbox.h - 2));
  return canvas.toDataURL("image/png");
}

function getContours(detection) {
  if (!detection.polygon || !detection.polygon.points_json) return [];

  const rawPoints = detection.polygon.points_json;
  if (typeof rawPoints === "string") {
    try {
      return JSON.parse(rawPoints);
    } catch (error) {
      console.error("Error parsing polygon crop points:", error);
      return [];
    }
  }

  return Array.isArray(rawPoints) ? rawPoints : [];
}

function getBoundsFromContours(contours) {
  const points = contours.flat();
  if (!points.length) return null;

  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  const minX = Math.floor(Math.min(...xs));
  const minY = Math.floor(Math.min(...ys));
  const maxX = Math.ceil(Math.max(...xs));
  const maxY = Math.ceil(Math.max(...ys));

  return {
    x: minX,
    y: minY,
    w: Math.max(1, maxX - minX),
    h: Math.max(1, maxY - minY),
  };
}

/**
 * Setup display mode controls
 * @param {ProductCanvas} productCanvas - Product canvas instance
 */
function setupDisplayModeControls(productCanvas) {
  const radioButtons = document.querySelectorAll('input[name="displayMode"]');
  radioButtons.forEach((radio) => {
    radio.addEventListener("change", function () {
      productCanvas.setDisplayMode(this.value);
    });
  });
}

/**
 * Setup download button
 * @param {HTMLElement} downloadBtn - Download button element
 * @param {ProductCanvas} productCanvas - Product canvas instance
 * @param {string} fileId - File ID
 * @param {string} originalUrl - Original image URL
 */
function setupDownloadButton(downloadBtn, productCanvas, fileId, originalUrl) {
  if (!downloadBtn) return;

  downloadBtn.addEventListener("click", async () => {
    const displayMode = productCanvas.displayMode;

    if (displayMode !== "image") {
      // Download canvas with overlay
      productCanvas.download(`product-${fileId}-${displayMode}.png`);
    } else {
      // Download original image via fetch to bypass cross-origin download restrictions
      try {
        const response = await fetch(originalUrl);
        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        
        const link = document.createElement("a");
        link.download = `product-${fileId}-original.jpg`;
        link.href = objectUrl;
        link.click();
        
        URL.revokeObjectURL(objectUrl);
      } catch (err) {
        console.error("Failed to download original image:", err);
      }
    }
  });
}

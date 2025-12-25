// productPage.js - Product detail page initialization

import { ProductCanvas } from "./productCanvas.js";

/**
 * Initialize product detail page
 */
export function initProductPage() {
  const canvas = document.getElementById("productCanvas");
  const originalImage = document.getElementById("originalImage");
  const detectionsDataEl = document.getElementById("detectionsData");
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

  downloadBtn.addEventListener("click", () => {
    const displayMode = productCanvas.displayMode;

    if (displayMode !== "image") {
      // Download canvas with overlay
      productCanvas.download(`product-${fileId}-${displayMode}.png`);
    } else {
      // Download original image
      const link = document.createElement("a");
      link.download = `product-${fileId}-original.jpg`;
      link.href = originalUrl;
      link.click();
    }
  });
}

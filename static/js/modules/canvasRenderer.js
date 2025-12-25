// canvasRenderer.js - Shared canvas rendering logic

import { CANVAS_COLORS } from "../utils/constants.js";
import { formatConfidence } from "../utils/formatters.js";

/**
 * CanvasRenderer class - Base canvas drawing functionality
 */
export class CanvasRenderer {
  constructor(canvasElement) {
    this.canvas = canvasElement;
    this.ctx = canvasElement ? canvasElement.getContext("2d") : null;
    this.currentImage = null;
  }

  /**
   * Load image onto canvas
   * @param {string} imageUrl - Image URL
   * @returns {Promise<HTMLImageElement>} Loaded image
   */
  loadImage(imageUrl) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        this.canvas.width = img.width;
        this.canvas.height = img.height;
        this.ctx.drawImage(img, 0, 0);
        this.currentImage = img;
        resolve(img);
      };
      img.onerror = reject;
      img.src = imageUrl;
    });
  }

  /**
   * Draw detections on canvas
   * @param {Array} objects - Detection objects
   */
  drawDetections(objects) {
    if (!objects || objects.length === 0) return;

    objects.forEach((obj, index) => {
      this.drawObject(obj, index);
    });
  }

  /**
   * Draw single detection object
   * @param {Object} obj - Detection object
   * @param {number} index - Object index for color selection
   */
  drawObject(obj, index) {
    const color = CANVAS_COLORS[index % CANVAS_COLORS.length];

    // Draw bounding box if available
    if (obj.bbox) {
      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 3;
      this.ctx.strokeRect(obj.bbox[0], obj.bbox[1], obj.bbox[2], obj.bbox[3]);

      // Draw label background
      this.ctx.fillStyle = color;
      this.ctx.fillRect(obj.bbox[0], obj.bbox[1] - 25, 150, 25);

      // Draw label text
      this.ctx.fillStyle = "#FFFFFF";
      this.ctx.font = "bold 14px Arial";
      this.ctx.fillText(
        `${obj.class_name} (${formatConfidence(obj.confidence)})`,
        obj.bbox[0] + 5,
        obj.bbox[1] - 7
      );
    }
  }

  /**
   * Clear canvas
   */
  clear() {
    if (this.ctx) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  }

  /**
   * Redraw current image
   */
  redrawImage() {
    if (this.currentImage) {
      this.ctx.drawImage(this.currentImage, 0, 0);
    }
  }

  /**
   * Download canvas as image
   * @param {string} filename - Download filename
   */
  download(filename = "canvas.png") {
    const link = document.createElement("a");
    link.download = filename;
    link.href = this.canvas.toDataURL("image/png");
    link.click();
  }

  /**
   * Render objects list in sidebar
   * @param {Array} objects - Detection objects
   * @param {HTMLElement} container - Container element
   */
  renderObjectsList(objects, container) {
    if (!container) return;

    container.innerHTML = "";
    objects.forEach((obj) => {
      const item = document.createElement("div");
      item.className = "stat-card stat-card--primary";
      item.innerHTML = `
        <div class="stat-card__value text-sm font-medium" style="color: #2E2E2E; font-size: 0.875rem;">
          ${obj.class_name}
        </div>
        <div class="stat-card__label" style="margin-bottom: 0; margin-top: 0.25rem;">
          Confidence: ${formatConfidence(obj.confidence)}
        </div>
      `;
      container.appendChild(item);
    });
  }
}

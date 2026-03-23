// productCanvas.js - Product detail page canvas rendering

import { TAG_COLORS } from "../utils/constants.js";
import { CanvasRenderer } from "./canvasRenderer.js";

const OVERLAY_PALETTE = [
  "#F25F5C",
  "#247BA0",
  "#70C1B3",
  "#FF9F1C",
  "#7F5AF0",
  "#2A9D8F",
  "#E76F51",
  "#3A86FF",
  "#EF476F",
  "#6A994E",
];

/**
 * ProductCanvas class - Extended canvas for product detail page
 */
export class ProductCanvas extends CanvasRenderer {
  constructor(canvasElement, detectionsData) {
    super(canvasElement);
    this.detections = detectionsData;
    this.displayMode = "polygon";
  }

  getDetectionColor(detection, index = 0) {
    return (
      detection.overlay_color ||
      OVERLAY_PALETTE[index % OVERLAY_PALETTE.length] ||
      TAG_COLORS[detection.label] ||
      "#999999"
    );
  }

  /**
   * Set display mode and redraw
   * @param {string} mode - Display mode (image, polygon, rectangle)
   */
  setDisplayMode(mode) {
    this.displayMode = mode;
    this.redraw();
  }

  /**
   * Redraw canvas based on current mode
   */
  redraw() {
    if (!this.ctx || !this.currentImage) return;

    // Clear and redraw original image
    this.clear();
    this.redrawImage();

    // Draw overlays based on mode
    if (this.displayMode !== "image" && this.detections.length > 0) {
      this.detections.forEach((detection, index) => {
        if (this.displayMode === "polygon") {
          this.drawDetectionPolygon(detection, index);
        } else if (this.displayMode === "rectangle") {
          this.drawDetectionRectangle(detection, index);
        }
      });
    }
  }

  /**
   * Draw detection with polygon overlay
   * @param {Object} detection - Detection object
   */
  drawDetectionPolygon(detection, index) {
    if (!detection.polygon || !detection.polygon.points_json) return;

    const color = this.getDetectionColor(detection, index);
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
        this.drawPolygon(contour, color);
      });
    }

    // Draw label
    this.drawLabel(detection, points, color);
  }

  /**
   * Draw detection with rectangle overlay
   * @param {Object} detection - Detection object
   */
  drawDetectionRectangle(detection, index) {
    const bbox = detection.bbox;
    if (!bbox) return;

    const color = this.getDetectionColor(detection, index);
    const { x, y, w, h } = bbox;

    // Set fill style with transparency
    this.ctx.fillStyle = color + "55";
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 3;

    // Draw filled rectangle
    this.ctx.fillRect(x, y, w, h);

    // Draw border
    this.ctx.strokeRect(x, y, w, h);

    // Draw label
    this.drawLabelAtPosition(detection.label, detection.confidence, x, y, color);
  }

  /**
   * Draw polygon contour
   * @param {Array} contour - Polygon contour points
   * @param {string} color - Color hex code
   */
  drawPolygon(contour, color) {
    if (!contour || contour.length === 0) return;

    // Set fill style with transparency
    this.ctx.fillStyle = color + "66";
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 3;

    this.ctx.beginPath();
    this.ctx.moveTo(contour[0].x, contour[0].y);

    for (let i = 1; i < contour.length; i++) {
      this.ctx.lineTo(contour[i].x, contour[i].y);
    }

    this.ctx.closePath();
    this.ctx.fill();
    this.ctx.stroke();
  }

  /**
   * Draw label for detection
   * @param {Object} detection - Detection object
   * @param {Array} points - Polygon points
   * @param {string} color - Color hex code
   */
  drawLabel(detection, points, color) {
    if (!points || points.length === 0 || points[0].length === 0) return;

    // Find top-left point from first contour
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

    this.drawLabelAtPosition(detection.label, detection.confidence, labelX, labelY, color);
  }

  /**
   * Draw label at specific position
   * @param {string} label - Class label
   * @param {number} confidence - Confidence score
   * @param {number} x - X position
   * @param {number} y - Y position
   * @param {string} color - Color hex code
   */
  drawLabelAtPosition(label, confidence, x, y, color) {
    const text = `${label} ${(confidence * 100).toFixed(0)}%`;

    this.ctx.font = "bold 14px Arial";
    const textMetrics = this.ctx.measureText(text);
    const textWidth = textMetrics.width;
    const textHeight = 18;
    const padding = 4;

    // Adjust position to stay within canvas
    const labelX = Math.max(
      0,
      Math.min(x, this.canvas.width - textWidth - padding * 2)
    );
    const labelY = Math.max(textHeight + padding * 2, y - 5);

    // Draw background
    this.ctx.fillStyle = color;
    this.ctx.fillRect(
      labelX,
      labelY - textHeight - padding,
      textWidth + padding * 2,
      textHeight + padding
    );

    // Draw text
    this.ctx.fillStyle = "#FFFFFF";
    this.ctx.fillText(text, labelX + padding, labelY - padding - 2);
  }
}

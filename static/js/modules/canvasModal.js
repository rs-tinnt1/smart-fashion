// canvasModal.js - Canvas modal management (shared across pages)

import { CanvasRenderer } from "./canvasRenderer.js";
import { show, hide } from "../utils/dom.js";

/**
 * Initialize canvas modal for upload page
 */
export function initCanvasModal() {
  const canvasModal = document.getElementById("canvasModal");
  const drawCanvas = document.getElementById("drawCanvas");
  const objectsList = document.getElementById("objectsList");
  const closeBtn = document.getElementById("closeCanvasBtn");
  const downloadBtn = document.getElementById("downloadCanvasBtn");

  if (!canvasModal || !drawCanvas) return;

  const canvasRenderer = new CanvasRenderer(drawCanvas);

  // Setup close button
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      closeModal(canvasModal);
    });
  }

  // Close on background click
  canvasModal.addEventListener("click", (e) => {
    if (e.target === canvasModal) {
      closeModal(canvasModal);
    }
  });

  // Close on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeModal(canvasModal);
    }
  });

  // Setup download button
  if (downloadBtn) {
    downloadBtn.addEventListener("click", () => {
      canvasRenderer.download("segmented-canvas.png");
    });
  }

  return {
    renderer: canvasRenderer,
    objectsList: objectsList,
    open: () => openModal(canvasModal),
    close: () => closeModal(canvasModal),
  };
}

/**
 * Open canvas modal
 * @param {HTMLElement} modal - Modal element
 */
function openModal(modal) {
  hide(modal);
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

/**
 * Close canvas modal
 * @param {HTMLElement} modal - Modal element
 */
function closeModal(modal) {
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

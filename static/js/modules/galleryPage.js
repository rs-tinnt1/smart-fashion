// imageActions.js - Gallery page image actions (delete, modal)

import { deleteImage as apiDeleteImage } from "../utils/api.js";

/**
 * Initialize gallery page
 */
export function initGalleryPage() {
  setupDeleteButtons();
  setupCanvasModal();
}

/**
 * Setup delete buttons for all gallery items
 */
function setupDeleteButtons() {
  const deleteButtons = document.querySelectorAll("[data-delete-image]");

  deleteButtons.forEach((button) => {
    button.addEventListener("click", async (e) => {
      e.preventDefault();
      const fileId = button.getAttribute("data-delete-image");

      if (!confirm("Are you sure you want to delete this image?")) {
        return;
      }

      try {
        await apiDeleteImage(fileId);
        window.location.reload();
      } catch (error) {
        console.error("Error deleting image:", error);
        alert("Failed to delete image. Please try again.");
      }
    });
  });
}

/**
 * Setup canvas modal (if needed for gallery)
 */
function setupCanvasModal() {
  const canvasModal = document.getElementById("canvasModal");
  if (!canvasModal) return;

  // Close modal on background click
  canvasModal.addEventListener("click", (e) => {
    if (e.target === canvasModal) {
      closeCanvasModal();
    }
  });

  // Close on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeCanvasModal();
    }
  });

  // Setup close button
  const closeBtn = document.getElementById("closeCanvasBtn");
  if (closeBtn) {
    closeBtn.addEventListener("click", closeCanvasModal);
  }
}

/**
 * Close canvas modal
 */
function closeCanvasModal() {
  const canvasModal = document.getElementById("canvasModal");
  if (canvasModal) {
    canvasModal.classList.add("hidden");
    canvasModal.classList.remove("flex");
  }
}

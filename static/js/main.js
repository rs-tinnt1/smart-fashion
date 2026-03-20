// main.js - ES Module Entry Point
// Router logic to initialize appropriate page module based on current page

function importVersionedModule(path) {
  const version = document.body?.dataset.appVersion || "dev";
  return import(`${path}?v=${encodeURIComponent(version)}`);
}

/**
 * Main application initialization
 */
document.addEventListener("DOMContentLoaded", async () => {
  // Detect current page from data-page attribute on body
  const currentPage = document.body.dataset.page;

  console.log(`[Fashion AI] Initializing page: ${currentPage}`);

  try {
    // Initialize page-specific modules
    switch (currentPage) {
      case "upload": {
        const [{ initUploadPage }, { initCanvasModal }] = await Promise.all([
          importVersionedModule("./modules/uploadPage.js"),
          importVersionedModule("./modules/canvasModal.js"),
        ]);
        initUploadPage();
        initCanvasModal();
        break;
      }

      case "gallery": {
        const { initGalleryPage } = await importVersionedModule("./modules/galleryPage.js");
        initGalleryPage();
        break;
      }

      case "product": {
        const { initProductPage } = await importVersionedModule("./modules/productPage.js");
        initProductPage();
        break;
      }

      default:
        console.warn(`[Fashion AI] Unknown page type: ${currentPage}`);
    }
  } catch (error) {
    console.error("[Fashion AI] Failed to initialize page modules", error);
  }

  // Apply dynamic styling enhancements
  applyDynamicStyling();
});

/**
 * Apply dynamic styling to dynamically generated content
 * This replaces the inline script from the old index.html
 */
function applyDynamicStyling() {
  // File List Styling Observer
  const fileList = document.getElementById("fileList");
  if (fileList) {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1 && node.classList) {
            // File items are already styled by uploadPage.js
            // This observer is kept for future extensibility
          }
        });
      });
    });
    observer.observe(fileList, { childList: true });
  }

  // Results Grid Styling Observer
  const resultsContainer = document.getElementById("resultsContainer");
  if (resultsContainer) {
    const resultsObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1 && node.classList) {
            // Gallery items are already styled by imageProcessor.js
            // This observer is kept for future extensibility
          }
        });
      });
    });
    resultsObserver.observe(resultsContainer, { childList: true });
  }

  // Canvas Modal Display Management
  const canvasModal = document.getElementById("canvasModal");
  if (canvasModal) {
    const modalObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === "class") {
          if (!canvasModal.classList.contains("hidden")) {
            canvasModal.classList.add("flex");
          } else {
            canvasModal.classList.remove("flex");
          }
        }
      });
    });
    modalObserver.observe(canvasModal, { attributes: true });
  }
}

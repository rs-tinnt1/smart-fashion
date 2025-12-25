// imageProcessor.js - Process images and display results

import { segmentImages } from "../utils/api.js";
import { show, hide, clearElement } from "../utils/dom.js";

/**
 * Process images through segmentation API
 * @param {FileHandler} fileHandler - File handler instance
 * @param {HTMLElement} resultsContainer - Results container element
 * @param {HTMLElement} loadingElement - Loading indicator element
 * @param {HTMLElement} processBtn - Process button element
 * @param {HTMLElement} resultsSection - Results section element
 */
export async function processImages(
  fileHandler,
  resultsContainer,
  loadingElement,
  processBtn,
  resultsSection
) {
  if (!fileHandler.hasFiles()) return;

  show(loadingElement);
  processBtn.disabled = true;
  clearElement(resultsContainer);
  hide(resultsSection);

  try {
    const response = await segmentImages(fileHandler.getFiles());
    displayResults(response.results, resultsContainer, resultsSection);
  } catch (error) {
    console.error("Error processing images:", error);
    alert("Failed to process images. Please try again.");
  } finally {
    hide(loadingElement);
    processBtn.disabled = false;
  }
}

/**
 * Display segmentation results
 * @param {Array} results - Segmentation results
 * @param {HTMLElement} container - Container element
 * @param {HTMLElement} section - Section element
 */
export function displayResults(results, container, section) {
  clearElement(container);

  results.forEach((result) => {
    const resultCard = createResultCard(result);
    container.appendChild(resultCard);
  });

  show(section);
  section.scrollIntoView({ behavior: "smooth" });
}

/**
 * Create result card element
 * @param {Object} result - Segmentation result
 * @returns {HTMLElement} Result card element
 */
function createResultCard(result) {
  const card = document.createElement("div");
  card.className = "gallery-item";

  const objects = result.segmentation_data?.objects || [];
  const objectsDetected = objects.length;
  const classes = [...new Set(objects.map((obj) => obj.class_name))];

  card.innerHTML = `
    <img src="${result.original_image_url}" alt="Segmented image" class="gallery-item__image">
    <div class="gallery-item__content">
      <div class="flex justify-between items-center mb-3">
        <span class="text-base font-medium text-charcoal">${objectsDetected} objects detected</span>
        <span class="text-xs text-fog">${result.filename}</span>
      </div>
      <div class="flex flex-wrap gap-2 mb-5">
        ${classes.map((cls) => `<span class="tag">${cls}</span>`).join("")}
      </div>
      <div class="flex gap-3 mt-5">
        <a href="${result.original_image_url}" download
           class="btn btn-primary flex-1 text-center text-sm">
          Download
        </a>
      </div>
    </div>
  `;

  return card;
}

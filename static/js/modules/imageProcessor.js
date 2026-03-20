// imageProcessor.js - Render segmentation results

import { show } from "../utils/dom.js";

export function prependResult(result, container, section) {
  const resultCard = createResultCard(result);
  container.prepend(resultCard);
  show(section);
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
  const previewUrl = result.preview_url || result.original_image_url || "";
  const detailUrl = result.file_id ? `/product/${result.file_id}` : "";
  const detailButton = detailUrl
    ? `<a href="${detailUrl}" class="btn btn-primary flex-1 text-center text-sm">View Details</a>`
    : `<span class="btn btn-primary flex-1 text-center text-sm opacity-60 pointer-events-none">Unavailable</span>`;

  card.innerHTML = `
    <img src="${previewUrl}" alt="Segmented image" class="gallery-item__image">
    <div class="gallery-item__content">
      <div class="flex justify-between items-center mb-3">
        <span class="text-base font-medium text-charcoal">${objectsDetected} objects detected</span>
        <span class="text-xs text-fog">${result.filename}</span>
      </div>
      <div class="flex flex-wrap gap-2 mb-5">
        ${classes.map((cls) => `<span class="tag">${cls}</span>`).join("")}
      </div>
      <div class="flex gap-3 mt-5">
        ${detailButton}
      </div>
    </div>
  `;

  return card;
}

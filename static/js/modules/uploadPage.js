// uploadPage.js - Upload page initialization and event handlers

import { FileHandler } from "./fileHandler.js";
import { processImages } from "./imageProcessor.js";
import { formatFileSize } from "../utils/formatters.js";
import { show, hide, clearElement } from "../utils/dom.js";

/**
 * Initialize upload page
 */
export function initUploadPage() {
  const fileHandler = new FileHandler();

  // Get DOM elements
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const filePreview = document.getElementById("filePreview");
  const fileList = document.getElementById("fileList");
  const processBtn = document.getElementById("processBtn");
  const loading = document.getElementById("loading");
  const resultsSection = document.getElementById("resultsSection");
  const resultsContainer = document.getElementById("resultsContainer");

  if (!dropZone || !fileInput) return;

  // Setup event listeners
  setupDropZoneEvents(dropZone, fileInput, fileHandler, fileList, filePreview);
  setupFileInputEvents(fileInput, fileHandler, fileList, filePreview);
  setupProcessButton(
    processBtn,
    fileHandler,
    resultsContainer,
    loading,
    resultsSection
  );
}

/**
 * Setup drop zone event handlers
 */
function setupDropZoneEvents(
  dropZone,
  fileInput,
  fileHandler,
  fileList,
  filePreview
) {
  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove("drag-over");

    const files = Array.from(e.dataTransfer.files).filter((file) =>
      file.type.startsWith("image/")
    );

    if (files.length > 0) {
      const validated = fileHandler.addFiles(files);
      if (validated.valid.length > 0) {
        updateFilePreview(fileHandler, fileList, filePreview);
      }
      if (validated.errors.length > 0) {
        showValidationErrors(validated.errors);
      }
    }
  });
}

/**
 * Setup file input event handlers
 */
function setupFileInputEvents(fileInput, fileHandler, fileList, filePreview) {
  fileInput.addEventListener("change", (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      const validated = fileHandler.addFiles(files);
      if (validated.valid.length > 0) {
        updateFilePreview(fileHandler, fileList, filePreview);
      }
      if (validated.errors.length > 0) {
        showValidationErrors(validated.errors);
      }
    }
  });
}

/**
 * Setup process button event handler
 */
function setupProcessButton(
  processBtn,
  fileHandler,
  resultsContainer,
  loading,
  resultsSection
) {
  if (!processBtn) return;

  processBtn.addEventListener("click", () => {
    processImages(
      fileHandler,
      resultsContainer,
      loading,
      processBtn,
      resultsSection
    );
  });
}

/**
 * Update file preview display
 */
function updateFilePreview(fileHandler, fileList, filePreview) {
  clearElement(fileList);

  const files = fileHandler.getFiles();
  files.forEach((file, index) => {
    const fileItem = createFileItem(file, index, fileHandler, fileList, filePreview);
    fileList.appendChild(fileItem);
  });

  show(filePreview);
}

/**
 * Create file item element
 */
function createFileItem(file, index, fileHandler, fileList, filePreview) {
  const fileItem = document.createElement("div");
  fileItem.className =
    "file-item flex items-center justify-between px-5 py-4 bg-white rounded-lg border border-light hover:border-dusty-blue transition-all duration-300";
  fileItem.style.borderLeft = "3px solid #6B8E9E";

  fileItem.innerHTML = `
    <div class="flex items-center">
      <svg class="w-5 h-5 text-dusty-blue mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
      </svg>
      <span class="text-sm font-medium text-charcoal">${file.name}</span>
      <span class="text-xs ml-3 text-fog">(${formatFileSize(file.size)})</span>
    </div>
    <button class="text-fog hover:text-red-500 transition-colors p-2 rounded-md" data-remove-index="${index}">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
    </button>
  `;

  // Add remove button event listener
  const removeBtn = fileItem.querySelector(`[data-remove-index="${index}"]`);
  removeBtn.addEventListener("click", () => {
    fileHandler.removeFile(index);
    if (fileHandler.hasFiles()) {
      updateFilePreview(fileHandler, fileList, filePreview);
    } else {
      hide(filePreview);
      document.getElementById("fileInput").value = "";
    }
  });

  return fileItem;
}

/**
 * Show validation errors
 */
function showValidationErrors(errors) {
  const errorHtml = errors.map((e) => `• ${e}`).join("\n");
  alert(`Upload Validation Errors:\n\n${errorHtml}`);
}

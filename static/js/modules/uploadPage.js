// uploadPage.js - Upload page initialization and event handlers

import { FileHandler } from "./fileHandler.js";
import { prependResult } from "./imageProcessor.js";
import { segmentImage } from "../utils/api.js";
import { formatFileSize } from "../utils/formatters.js";
import { show, hide, clearElement } from "../utils/dom.js";

/**
 * Initialize upload page
 */
export function initUploadPage() {
  const fileHandler = new FileHandler();
  let isProcessing = false;

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
  setupDropZoneEvents(dropZone, fileInput, fileHandler, fileList, filePreview, processBtn);
  setupFileInputEvents(fileInput, fileHandler, fileList, filePreview, processBtn);
  setupProcessButton(
    processBtn,
    fileHandler,
    fileList,
    filePreview,
    resultsContainer,
    loading,
    resultsSection,
    fileInput,
    () => isProcessing,
    (value) => {
      isProcessing = value;
    }
  );

  updateQueueSummary(fileHandler, processBtn);
}

/**
 * Setup drop zone event handlers
 */
function setupDropZoneEvents(
  dropZone,
  fileInput,
  fileHandler,
  fileList,
  filePreview,
  processBtn
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
        updateFilePreview(fileHandler, fileList, filePreview, processBtn);
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
function setupFileInputEvents(fileInput, fileHandler, fileList, filePreview, processBtn) {
  fileInput.addEventListener("change", (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      const validated = fileHandler.addFiles(files);
      if (validated.valid.length > 0) {
        updateFilePreview(fileHandler, fileList, filePreview, processBtn);
      }
      if (validated.errors.length > 0) {
        showValidationErrors(validated.errors);
      }
    }
    fileInput.value = "";
  });
}

/**
 * Setup process button event handler
 */
function setupProcessButton(
  processBtn,
  fileHandler,
  fileList,
  filePreview,
  resultsContainer,
  loading,
  resultsSection,
  fileInput,
  getIsProcessing,
  setIsProcessing
) {
  if (!processBtn) return;

  processBtn.addEventListener("click", async () => {
    if (getIsProcessing() || !fileHandler.hasFiles()) return;

    if (!fileHandler.getNextWaitingFile()) {
      fileHandler.retryFailed();
      updateFilePreview(fileHandler, fileList, filePreview, processBtn, false);
    }

    setIsProcessing(true);
    show(loading);
    updateQueueSummary(fileHandler, processBtn, true);

    while (true) {
      const job = fileHandler.getNextWaitingFile();
      if (!job) break;

      fileHandler.markProcessing(job.id);
      updateFilePreview(fileHandler, fileList, filePreview, processBtn, true);

      try {
        const result = await segmentImage(job.file);
        prependResult(
          {
            ...result,
            filename: result.filename || job.file.name,
            preview_url: URL.createObjectURL(job.file),
          },
          resultsContainer,
          resultsSection
        );
        fileHandler.removeFile(job.id);
      } catch (error) {
        console.error("Error processing image:", error);
        fileHandler.markFailed(job.id, error.message || "Processing failed");
      }

      updateFilePreview(fileHandler, fileList, filePreview, processBtn, true);
    }

    setIsProcessing(false);
    hide(loading);
    updateFilePreview(fileHandler, fileList, filePreview, processBtn, false);
    if (!fileHandler.hasFiles()) {
      fileInput.value = "";
    }
  });
}

/**
 * Update file preview display
 */
function updateFilePreview(fileHandler, fileList, filePreview, processBtn, isProcessing = false) {
  clearElement(fileList);

  const files = fileHandler.getFiles();
  files.forEach((job) => {
    const fileItem = createFileItem(job, fileHandler, fileList, filePreview, processBtn, isProcessing);
    fileList.appendChild(fileItem);
  });

  if (files.length > 0) {
    show(filePreview);
  } else {
    hide(filePreview);
  }

  updateQueueSummary(fileHandler, processBtn, isProcessing);
}

/**
 * Create file item element
 */
function createFileItem(job, fileHandler, fileList, filePreview, processBtn, isProcessing) {
  const statusColor = {
    waiting: "#9AA3AE",
    processing: "#6B8E9E",
    failed: "#C75B39",
  };
  const statusLabel = {
    waiting: "Waiting",
    processing: "Processing",
    failed: "Failed",
  };
  const fileItem = document.createElement("div");
  fileItem.className =
    "file-item flex items-center justify-between px-5 py-4 bg-white rounded-lg border border-light hover:border-dusty-blue transition-all duration-300";
  fileItem.style.borderLeft = `3px solid ${statusColor[job.status] || "#6B8E9E"}`;

  fileItem.innerHTML = `
    <div class="flex items-center">
      <svg class="w-5 h-5 text-dusty-blue mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
      </svg>
      <div>
        <div>
          <span class="text-sm font-medium text-charcoal">${job.file.name}</span>
          <span class="text-xs ml-3 text-fog">(${formatFileSize(job.file.size)})</span>
        </div>
        <div class="text-xs mt-1" style="color: ${statusColor[job.status] || "#6B8E9E"}">
          ${statusLabel[job.status] || "Waiting"}${job.error ? ` - ${job.error}` : ""}
        </div>
      </div>
    </div>
    <button class="text-fog hover:text-red-500 transition-colors p-2 rounded-md" data-remove-id="${job.id}">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
    </button>
  `;

  // Add remove button event listener
  const removeBtn = fileItem.querySelector(`[data-remove-id="${job.id}"]`);
  removeBtn.addEventListener("click", () => {
    fileHandler.removeFile(job.id);
    if (fileHandler.hasFiles()) {
      updateFilePreview(fileHandler, fileList, filePreview, processBtn, isProcessing);
    } else {
      hide(filePreview);
      document.getElementById("fileInput").value = "";
      updateQueueSummary(fileHandler, processBtn, isProcessing);
    }
  });

  return fileItem;
}

function updateQueueSummary(fileHandler, processBtn, isProcessing = false) {
  if (!processBtn) return;

  const total = fileHandler.getFiles().length;
  const waiting = fileHandler.countByStatus("waiting");
  const processing = fileHandler.countByStatus("processing");
  const failed = fileHandler.countByStatus("failed");

  if (total === 0) {
    processBtn.disabled = true;
    processBtn.textContent = "Queue Is Empty";
    return;
  }

  if (!isProcessing && waiting === 0 && processing === 0 && failed > 0) {
    processBtn.disabled = false;
    processBtn.textContent = `Retry Failed (${failed})`;
    return;
  }

  processBtn.disabled = isProcessing;
  processBtn.textContent = isProcessing
    ? `Queue Running (${processing || 1} processing, ${waiting} waiting)`
    : `Process Queue (${total}/100)`;
}

/**
 * Show validation errors
 */
function showValidationErrors(errors) {
  const errorHtml = errors.map((e) => `• ${e}`).join("\n");
  alert(`Upload Validation Errors:\n\n${errorHtml}`);
}

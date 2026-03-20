// fileHandler.js - Handle file validation and management

import { MAX_FILES, MAX_FILE_SIZE_BYTES } from "../utils/constants.js";
import { formatFileSize } from "../utils/formatters.js";

/**
 * FileHandler class - Manages file selection, validation, and removal
 */
export class FileHandler {
  constructor() {
    this.selectedFiles = [];
  }

  /**
   * Validate files against size and count limits
   * @param {File[]} files - Files to validate
   * @returns {Object} Object with valid files and error messages
   */
  validateFiles(files) {
    const result = { valid: [], errors: [] };
    const remainingSlots = Math.max(0, MAX_FILES - this.selectedFiles.length);

    if (remainingSlots === 0) {
      result.errors.push(`Queue is full. Maximum ${MAX_FILES} files allowed.`);
      return result;
    }

    if (files.length > remainingSlots) {
      result.errors.push(
        `Only ${remainingSlots} queue slots left. Extra files were ignored.`
      );
      files = files.slice(0, remainingSlots);
    }

    files.forEach((file) => {
      if (file.size > MAX_FILE_SIZE_BYTES) {
        result.errors.push(
          `${file.name}: File size ${formatFileSize(file.size)} exceeds ${
            MAX_FILE_SIZE_BYTES / 1024
          }KB limit`
        );
      } else {
        result.valid.push(file);
      }
    });

    return result;
  }

  /**
   * Add files to selection
   * @param {File[]} newFiles - Files to add
   * @returns {Object} Validation result
   */
  addFiles(newFiles) {
    const validated = this.validateFiles(newFiles);
    if (validated.valid.length > 0) {
      this.selectedFiles.push(
        ...validated.valid.map((file) => ({
          id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
          file,
          status: "waiting",
          error: "",
        }))
      );
    }
    return validated;
  }

  /**
   * Remove file at index
   * @param {number} index - Index of file to remove
   */
  removeFile(id) {
    this.selectedFiles = this.selectedFiles.filter((job) => job.id !== id);
  }

  /**
   * Get all selected files
   * @returns {File[]} Selected files
   */
  getFiles() {
    return this.selectedFiles;
  }

  getNextWaitingFile() {
    return this.selectedFiles.find((job) => job.status === "waiting") || null;
  }

  markProcessing(id) {
    const job = this.selectedFiles.find((item) => item.id === id);
    if (job) {
      job.status = "processing";
      job.error = "";
    }
  }

  markFailed(id, error) {
    const job = this.selectedFiles.find((item) => item.id === id);
    if (job) {
      job.status = "failed";
      job.error = error;
    }
  }

  retryFailed() {
    this.selectedFiles.forEach((job) => {
      if (job.status === "failed") {
        job.status = "waiting";
        job.error = "";
      }
    });
  }

  countByStatus(status) {
    return this.selectedFiles.filter((job) => job.status === status).length;
  }

  /**
   * Clear all selected files
   */
  clear() {
    this.selectedFiles = [];
  }

  /**
   * Check if files are selected
   * @returns {boolean} True if files are selected
   */
  hasFiles() {
    return this.selectedFiles.length > 0;
  }
}

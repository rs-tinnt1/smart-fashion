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

    // Check max files
    if (files.length > MAX_FILES) {
      result.errors.push(
        `Maximum ${MAX_FILES} files allowed. You selected ${files.length} files.`
      );
      files = files.slice(0, MAX_FILES);
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
      this.selectedFiles = validated.valid;
    }
    return validated;
  }

  /**
   * Remove file at index
   * @param {number} index - Index of file to remove
   */
  removeFile(index) {
    this.selectedFiles.splice(index, 1);
  }

  /**
   * Get all selected files
   * @returns {File[]} Selected files
   */
  getFiles() {
    return this.selectedFiles;
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

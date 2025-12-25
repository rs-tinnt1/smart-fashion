// formatters.js - Utility functions for formatting data

/**
 * Format file size in bytes to human-readable string
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}

/**
 * Format timestamp to locale date string
 * @param {string|number} timestamp - Timestamp
 * @returns {string} Formatted date
 */
export function formatDate(timestamp) {
  return new Date(timestamp).toLocaleDateString();
}

/**
 * Format confidence score to percentage
 * @param {number} confidence - Confidence score (0-1)
 * @returns {string} Formatted percentage
 */
export function formatConfidence(confidence) {
  return (confidence * 100).toFixed(1) + "%";
}

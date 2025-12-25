// api.js - API communication utilities

/**
 * Segment images via API
 * @param {File[]} files - Array of image files
 * @returns {Promise<Object>} API response with segmentation results
 */
export async function segmentImages(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch("/api/segment", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Processing failed");
  }

  return response.json();
}

/**
 * Delete image by ID
 * @param {string} fileId - Image file ID
 * @returns {Promise<Object>} API response
 */
export async function deleteImage(fileId) {
  const response = await fetch(`/api/delete/${fileId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("Failed to delete image");
  }

  return response.json();
}

/**
 * Get image details by ID
 * @param {string} fileId - Image file ID
 * @returns {Promise<Object>} Image details with detections
 */
export async function getImageDetails(fileId) {
  const response = await fetch(`/api/details/${fileId}`);

  if (!response.ok) {
    throw new Error("Failed to fetch details");
  }

  return response.json();
}

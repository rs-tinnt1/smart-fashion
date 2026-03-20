// api.js - API communication utilities

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function readErrorMessage(response) {
  try {
    const data = await response.json();
    return data.detail || data.message || `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}

/**
 * Upload a single image and create a background job.
 * @param {File} file - Image file
 * @returns {Promise<Object>} Upload response with job metadata
 */
export async function uploadImage(file) {
  const formData = new FormData();
  formData.append("file", file);

  for (let attempt = 1; attempt <= 2; attempt += 1) {
    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      return response.json();
    }

    if (response.status === 503 && attempt < 2) {
      await sleep(6000);
      continue;
    }

    throw new Error(await readErrorMessage(response));
  }

  throw new Error("Upload failed");
}

/**
 * Get background job status.
 * @param {string} jobId - Job identifier
 * @returns {Promise<Object>} Job status payload
 */
export async function getJobStatus(jobId) {
  const response = await fetch(`/api/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json();
}

/**
 * Get processed image details.
 * @param {string} imageId - Image identifier
 * @returns {Promise<Object>} Image payload
 */
export async function getImage(imageId) {
  const response = await fetch(`/api/images/${imageId}`);
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json();
}

/**
 * Upload multiple images sequentially.
 * @param {File[]} files - Array of image files
 * @returns {Promise<Object[]>} Upload responses
 */
export async function uploadImages(files) {
  const results = [];
  for (const file of files) {
    results.push(await uploadImage(file));
  }
  return results;
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

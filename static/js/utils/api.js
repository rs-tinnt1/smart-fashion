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
 * Segment a single image via API with light retry for Render cold starts.
 * @param {File} file - Image file
 * @returns {Promise<Object>} First segmentation result
 */
export async function segmentImage(file) {
  const formData = new FormData();
  formData.append("files", file);

  for (let attempt = 1; attempt <= 2; attempt += 1) {
    const response = await fetch("/api/segment", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      const payload = await response.json();
      return payload.results?.[0] || payload;
    }

    if (response.status === 503 && attempt < 2) {
      await sleep(6000);
      continue;
    }

    throw new Error(await readErrorMessage(response));
  }

  throw new Error("Processing failed");
}

/**
 * Segment multiple images sequentially.
 * @param {File[]} files - Array of image files
 * @returns {Promise<Object[]>} Segmentation results
 */
export async function segmentImages(files) {
  const results = [];
  for (const file of files) {
    results.push(await segmentImage(file));
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

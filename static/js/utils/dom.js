// dom.js - DOM manipulation utilities

/**
 * Show element by removing 'hidden' class
 * @param {HTMLElement} element - Element to show
 */
export function show(element) {
  if (element) {
    element.classList.remove("hidden");
  }
}

/**
 * Hide element by adding 'hidden' class
 * @param {HTMLElement} element - Element to hide
 */
export function hide(element) {
  if (element) {
    element.classList.add("hidden");
  }
}

/**
 * Toggle class on element
 * @param {HTMLElement} element - Element to toggle
 * @param {string} className - Class name to toggle
 */
export function toggleClass(element, className) {
  if (element) {
    element.classList.toggle(className);
  }
}

/**
 * Add class to element
 * @param {HTMLElement} element - Element
 * @param {string} className - Class name to add
 */
export function addClass(element, className) {
  if (element) {
    element.classList.add(className);
  }
}

/**
 * Remove class from element
 * @param {HTMLElement} element - Element
 * @param {string} className - Class name to remove
 */
export function removeClass(element, className) {
  if (element) {
    element.classList.remove(className);
  }
}

/**
 * Clear element's inner HTML
 * @param {HTMLElement} element - Element to clear
 */
export function clearElement(element) {
  if (element) {
    element.innerHTML = "";
  }
}

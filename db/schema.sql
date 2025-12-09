-- Smart Fashion Database Schema
-- MariaDB 11.x compatible

-- Drop tables if exist (for clean re-creation)
DROP TABLE IF EXISTS product_tags;
DROP TABLE IF EXISTS embeddings;
DROP TABLE IF EXISTS polygons;
DROP TABLE IF EXISTS detections;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS images;

-- Images table
CREATE TABLE images (
    id CHAR(36) PRIMARY KEY,
    storage_url VARCHAR(512) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    width INT NOT NULL DEFAULT 0,
    height INT NOT NULL DEFAULT 0,
    file_size INT NOT NULL DEFAULT 0,
    hash VARCHAR(64) NULL,
    INDEX idx_images_uploaded_at (uploaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Jobs table for async processing
CREATE TABLE jobs (
    id CHAR(36) PRIMARY KEY,
    image_id CHAR(36) NOT NULL,
    status ENUM('pending', 'processing', 'done', 'error') DEFAULT 'pending',
    error_message TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
    INDEX idx_jobs_status (status),
    INDEX idx_jobs_image_id (image_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Detections table
CREATE TABLE detections (
    id CHAR(36) PRIMARY KEY,
    image_id CHAR(36) NOT NULL,
    label VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    bbox_x INT NOT NULL,
    bbox_y INT NOT NULL,
    bbox_w INT NOT NULL,
    bbox_h INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
    INDEX idx_detections_image_id (image_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Polygons table (1:1 with detections)
CREATE TABLE polygons (
    id CHAR(36) PRIMARY KEY,
    detection_id CHAR(36) NOT NULL UNIQUE,
    points_json JSON NOT NULL,
    simplified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Embeddings table (1:1 with detections)
CREATE TABLE embeddings (
    id CHAR(36) PRIMARY KEY,
    detection_id CHAR(36) NOT NULL UNIQUE,
    model_name VARCHAR(100) NOT NULL,
    `vector` JSON NOT NULL,
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Product tags table (1:N with detections)
CREATE TABLE product_tags (
    id CHAR(36) PRIMARY KEY,
    detection_id CHAR(36) NOT NULL,
    tag_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE,
    INDEX idx_product_tags_detection_id (detection_id),
    INDEX idx_product_tags_tag_name (tag_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

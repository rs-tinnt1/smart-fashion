# Integration Tests - Bottom-Up Approach

## Overview

This document contains integration test scenarios for the Smart Fashion API.
Tests are structured using **Bottom-Up Integration** strategy:

1. **Level 1**: Infrastructure (Database, MinIO)
2. **Level 2**: Services (DatabaseService, MinIOService)
3. **Level 3**: API Endpoints
4. **Level 4**: Frontend UI Flows

---

## Level 1: Infrastructure Layer

### INT-INFRA-001: MariaDB Connection

```
Test Case ID: INT-INFRA-001
Module(s) Under Test: MariaDB Container
Pre-conditions:
    - Docker/Podman is running
    - compose.yml is correctly configured
Test Steps:
    1. Run: podman compose up -d mariadb
    2. Wait for healthcheck to pass
    3. Connect to MariaDB: podman exec -it mariadb mysql -usmartfashion -psmartfashion smartfashion
    4. Run: SHOW TABLES;
Expected Results:
    1. Container starts without errors
    2. Healthcheck passes within 30s
    3. MySQL client connects successfully
    4. Tables exist: images, jobs, detections, polygons, embeddings, product_tags
Pass/Fail Status: [ ]
Defect ID:
```

### INT-INFRA-002: MinIO Connection and Bucket

```
Test Case ID: INT-INFRA-002
Module(s) Under Test: MinIO Container
Pre-conditions:
    - Docker/Podman is running
    - MINIO_ROOT_USER and MINIO_ROOT_PASSWORD are set in .env
Test Steps:
    1. Run: podman compose up -d minio
    2. Access MinIO Console: http://localhost:9001
    3. Login with credentials from .env
    4. Check if bucket "smartfashion" exists (or create it)
    5. Upload a test file manually
    6. Access file via presigned URL
Expected Results:
    1. Container starts, ports 9000 and 9001 are exposed
    2. Console is accessible
    3. Login successful
    4. Bucket exists or can be created
    5. File upload successful
    6. File accessible via http://localhost:9000/...
Pass/Fail Status: [ ]
Defect ID:
```

### INT-INFRA-003: MinIO MINIO_SERVER_URL Configuration

```
Test Case ID: INT-INFRA-003
Module(s) Under Test: MinIO Presigned URL Configuration
Pre-conditions:
    - MinIO container is running
Test Steps:
    1. Check MinIO container environment: podman exec minio env | grep MINIO
    2. Verify MINIO_SERVER_URL is set to http://localhost:9000
    3. Generate presigned URL via mc: podman exec minio mc share download local/smartfashion/<any-file>
    4. Verify URL contains "localhost:9000" not "minio:9000"
Expected Results:
    1. MINIO_SERVER_URL=http://localhost:9000 is present
    2. Configuration is correct
    3. Presigned URL generated successfully
    4. URL host is "localhost:9000"
Pass/Fail Status: [ ]
Defect ID:
```

---

## Level 2: Service Layer

### INT-SVC-001: DatabaseService - Connection Pool

```
Test Case ID: INT-SVC-001
Module(s) Under Test: app.services.database.DatabaseService
Pre-conditions:
    - MariaDB is running and healthy
    - DB credentials are correct in environment
Test Steps:
    1. Start app container
    2. Check logs for "Database pool initialized"
    3. Execute: podman exec smartfashion python -c "
       import asyncio
       from app.services.database import get_database
       asyncio.run(get_database())"
Expected Results:
    1. App container starts
    2. Log message appears: "Database pool initialized: mariadb:3306/smartfashion"
    3. No connection errors
Pass/Fail Status: [ ]
Defect ID:
```

### INT-SVC-002: DatabaseService - CRUD Operations

```
Test Case ID: INT-SVC-002
Module(s) Under Test: DatabaseService create/get methods
Pre-conditions:
    - DatabaseService connection established
Test Steps:
    1. Create image: await db.create_image(image_id, storage_url, width, height, file_size, hash)
    2. Get image: await db.get_image(image_id)
    3. Create detection: await db.create_detection(image_id, label, confidence, bbox...)
    4. Get detection: await db.get_detection(detection_id)
Expected Results:
    1. Image created, no errors
    2. Image retrieved with correct data
    3. Detection created, returns detection_id
    4. Detection retrieved with polygon and embedding data
Pass/Fail Status: [ ]
Defect ID:
```

### INT-SVC-003: MinIOService - Upload and Download

```
Test Case ID: INT-SVC-003
Module(s) Under Test: app.services.minio_service.MinIOService
Pre-conditions:
    - MinIO is running
    - Bucket "smartfashion" exists
Test Steps:
    1. Initialize MinIOService
    2. Upload bytes: minio.upload_bytes(data, "test/test.txt")
    3. Check exists: minio.object_exists("test/test.txt")
    4. Download: minio.download_file("test/test.txt", "/tmp/test.txt")
    5. Delete: minio.delete_object("test/test.txt")
Expected Results:
    1. Service initialized without errors
    2. Upload returns True
    3. object_exists returns True
    4. File downloaded successfully
    5. Object deleted
Pass/Fail Status: [ ]
Defect ID:
```

### INT-SVC-004: MinIOService - Presigned URL Generation

```
Test Case ID: INT-SVC-004
Module(s) Under Test: MinIOService.get_presigned_url
Pre-conditions:
    - MinIO is running with MINIO_SERVER_URL=http://localhost:9000
    - MINIO_EXTERNAL_ENDPOINT=http://localhost:9000 in app config
    - A test object exists in bucket
Test Steps:
    1. Call minio.get_presigned_url("uploads/test.jpg")
    2. Parse returned URL
    3. Access URL via HTTP GET
Expected Results:
    1. URL returned (not None)
    2. URL host is "localhost:9000" (NOT "minio:9000")
    3. HTTP 200 response (NOT 403 Forbidden)
Pass/Fail Status: [ ]
Defect ID:
```

---

## Level 3: API Endpoint Layer

### INT-API-001: Health Check Endpoint

```
Test Case ID: INT-API-001
Module(s) Under Test: GET /api/health
Pre-conditions:
    - App container is running
Test Steps:
    1. GET http://localhost:8000/api/health
    2. Parse JSON response
Expected Results:
    1. HTTP 200
    2. Response: {"status": "healthy", "model_loaded": true, "timestamp": "..."}
Pass/Fail Status: [ ]
Defect ID:
```

### INT-API-002: Segment Endpoint - Process Image

```
Test Case ID: INT-API-002
Module(s) Under Test: POST /api/segment
Pre-conditions:
    - App is running, model loaded
    - Test image file exists (< 500KB)
Test Steps:
    1. POST /api/segment with files=@test.jpg
    2. Parse response JSON
    3. Verify file_id is UUID format
    4. Verify segmentation_data.objects exists
Expected Results:
    1. HTTP 200
    2. Response contains: success: true, results: [...]
    3. file_id is valid UUID
    4. objects array contains detected clothing items
Pass/Fail Status: [ ]
Defect ID:
```

### INT-API-003: Segment Endpoint - Database Saving

```
Test Case ID: INT-API-003
Module(s) Under Test: POST /api/segment → DatabaseService
Pre-conditions:
    - Database is empty or count is known
Test Steps:
    1. Count images in database before
    2. POST /api/segment with test image
    3. Extract file_id from response
    4. Query database for image with file_id
    5. Query detections for that image_id
Expected Results:
    1. Initial count noted
    2. Segment succeeds
    3. file_id extracted
    4. Image record exists in database
    5. Detection records exist with labels
Pass/Fail Status: [ ]
Defect ID:
```

### INT-API-004: Segment Endpoint - Presigned URL in Response

```
Test Case ID: INT-API-004
Module(s) Under Test: POST /api/segment → MinIOService.get_presigned_url
Pre-conditions:
    - App running with correct MinIO config
Test Steps:
    1. POST /api/segment with test image
    2. Extract output_image_url from response
    3. Parse URL host
    4. HTTP GET the URL
Expected Results:
    1. Segment succeeds
    2. output_image_url is returned
    3. URL host is "localhost:9000"
    4. HTTP 200, image data returned
Pass/Fail Status: [ ]
Defect ID:
```

### INT-API-005: Gallery API Endpoint

```
Test Case ID: INT-API-005
Module(s) Under Test: GET /api/gallery
Pre-conditions:
    - At least 1 processed image in database
Test Steps:
    1. GET http://localhost:8000/api/gallery
    2. Parse images array
    3. Verify each image has original_url and detections
    4. Test original_url accessibility
Expected Results:
    1. HTTP 200
    2. images array is not empty
    3. Each image has id, original_url, detection_count
    4. URLs return HTTP 200 (not 403)
Pass/Fail Status: [ ]
Defect ID:
```

### INT-API-006: File Size Validation

```
Test Case ID: INT-API-006
Module(s) Under Test: POST /api/segment (validation)
Pre-conditions:
    - Test image > 500KB
Test Steps:
    1. POST /api/segment with large file
Expected Results:
    1. HTTP 400
    2. Error message: "File size exceeds maximum allowed"
Pass/Fail Status: [ ]
Defect ID:
```

---

## Level 4: Frontend UI Layer

### INT-UI-001: Home Page Load

```
Test Case ID: INT-UI-001
Module(s) Under Test: index.html, home.js
Pre-conditions:
    - App is running
Test Steps:
    1. Navigate to http://localhost:8000/
    2. Verify page elements are present
Expected Results:
    1. Page loads without errors
    2. Upload dropzone is visible
    3. File size limit text shows "Max 100 files | Max 500KB each"
Pass/Fail Status: [ ]
Defect ID:
```

### INT-UI-002: Home Page - Upload and Display Results

```
Test Case ID: INT-UI-002
Module(s) Under Test: home.js → /api/segment → Display
Pre-conditions:
    - App running, model loaded
    - Valid test image available
Test Steps:
    1. Open home page
    2. Upload image via drag-drop or file picker
    3. Click "Process Images"
    4. Wait for results
    5. Verify result image is displayed
    6. Click on result image
Expected Results:
    1. Page loads
    2. File appears in preview list
    3. Loading spinner appears
    4. Results section shows processed image
    5. Image loads (not broken image icon)
    6. Image opens in modal or new tab
Pass/Fail Status: [ ]
Defect ID:
```

### INT-UI-003: Gallery Page - Display from Database

```
Test Case ID: INT-UI-003
Module(s) Under Test: gallery.html → /api/gallery → Display
Pre-conditions:
    - Processed images exist in database
Test Steps:
    1. Navigate to http://localhost:8000/gallery
    2. Verify image grid is displayed
    3. Verify detection labels are shown
    4. Click on image thumbnail
Expected Results:
    1. Gallery page loads
    2. Image cards are displayed
    3. Labels like "long_sleeved_shirt" are visible
    4. Image modal opens with full-size image
Pass/Fail Status: [ ]
Defect ID:
```

---

## Test Execution Order (Bottom-Up)

Execute tests in this order to follow bottom-up integration:

| Phase | Tests        | Description          |
| ----- | ------------ | -------------------- |
| 1     | INT-INFRA-\* | Infrastructure layer |
| 2     | INT-SVC-\*   | Service layer        |
| 3     | INT-API-\*   | API endpoint layer   |
| 4     | INT-UI-\*    | Frontend UI layer    |

## Test Execution Checklist

| Test ID       | Level | Status | Tester | Date | Notes |
| ------------- | ----- | ------ | ------ | ---- | ----- |
| INT-INFRA-001 | 1     |        |        |      |       |
| INT-INFRA-002 | 1     |        |        |      |       |
| INT-INFRA-003 | 1     |        |        |      |       |
| INT-SVC-001   | 2     |        |        |      |       |
| INT-SVC-002   | 2     |        |        |      |       |
| INT-SVC-003   | 2     |        |        |      |       |
| INT-SVC-004   | 2     |        |        |      |       |
| INT-API-001   | 3     |        |        |      |       |
| INT-API-002   | 3     |        |        |      |       |
| INT-API-003   | 3     |        |        |      |       |
| INT-API-004   | 3     |        |        |      |       |
| INT-API-005   | 3     |        |        |      |       |
| INT-API-006   | 3     |        |        |      |       |
| INT-UI-001    | 4     |        |        |      |       |
| INT-UI-002    | 4     |        |        |      |       |
| INT-UI-003    | 4     |        |        |      |       |

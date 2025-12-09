# Database Design

# Sơ đồ mermaid

```mermaid
classDiagram

class images {
  int id PK
  varchar storage_url
  datetime uploaded_at
  int width
  int height
  int file_size
  varchar hash
}

class detections {
  int id PK
  int image_id FK
  varchar label
  float confidence
  int bbox_x
  int bbox_y
  int bbox_w
  int bbox_h
}

class polygons {
  int id PK
  int detection_id FK
  json points_json
  bool simplified
}

class embeddings {
  int id PK
  int detection_id FK
  varchar model_name
  text vector
}

class product_tags {
  int id PK
  int detection_id FK
  varchar tag_name
}

images --> detections : 1..N
detections --> polygons : 1..1
detections --> embeddings : 1..1
detections --> product_tags : 1..N

```

# Sơ đồ ascii

```asciidoc
+------------------+
|     images       |
+------------------+
| id (PK)          |
| storage_url       |
| uploaded_at       |
| width             |
| height            |
| file_size         |
| hash              |
+------------------+
          |
          | 1:N
          v
+---------------------------+
|       detections          |
+---------------------------+
| id (PK)                   |
| image_id (FK->images)     |
| label (e.g. shirt, pant)  |
| confidence                |
| bbox_x                    |
| bbox_y                    |
| bbox_w                    |
| bbox_h                    |
+---------------------------+
          |
          | 1:1 (optional)
          v
+---------------------------+
|       polygons            |
+---------------------------+
| id (PK)                   |
| detection_id (FK)         |
| points_json (JSON array)  |
| simplified (bool)         |
+---------------------------+

          |
          | 1:1 (optional)
          v
+---------------------------+
|       embeddings          |
+---------------------------+
| id (PK)                   |
| detection_id (FK)         |
| model_name                |
| vector (JSON or TEXT)     |
+---------------------------+


+---------------------------+
|      product_tags         |
+---------------------------+
| id (PK)                   |
| detection_id (FK)         |
| tag_name                  |
+---------------------------+

```

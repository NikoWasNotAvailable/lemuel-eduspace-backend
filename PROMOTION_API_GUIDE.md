# Promotion System API Guide for Frontend

This guide explains how to implement the mass promotion UI using the backend APIs.

## Overview

The promotion system allows admins to automatically promote students to the next grade level (e.g., SD1 -> SD2) and assign them to classes in the new grade. 

**Key Features:**
- **Deterministic Assignment**: Students are essentially distributed round-robin into available classes of the next grade.
- **Preview First**: Always preview changes before applying them to the database.
- **Safety**: Supports excluding specific students from promotion.
- **Undo**: Any applied promotion can be fully reverted.

## 1. The Promotion Workflow (Preview -> Confirm)

The UI should essentially follow this flow:

1.  **User clicks "Start Promotion"**
2.  **Frontend calls `POST /preview`**
    -   Displays the "Proposed Changes" to the user.
    -   Shows summary (e.g., "50 Students to Promote, 10 to Graduate").
    -   Shows list of students with their Old Class -> New Class mapping.
    -   Allows user to select students to **exclude**.
3.  **User clicks "Confirm Promotion"**
    -   Frontend calls `POST /confirm` with the list of excluded student IDs.
    -   Backend applies changes and saves a history record.
4.  **Success**: Show success message and redirect to History.

### API: Preview Changes

**Endpoint:** `POST /api/v1/promotions/preview`

**Request Body:**
```json
{
  "exclude_student_ids": [] // Optional: IDs of students to skip
}
```

**Response:**
```json
{
  "summary": {
    "promoted": 45,
    "graduated": 5,
    "no_class_available": 0,
    "error": 0
  },
  "details": [
    {
      "student_id": 101,
      "student_name": "John Doe",
      "old_grade": "SD1",
      "old_class_id": 10,
      "old_class_name": "SD1 A",
      "new_grade": "SD2",
      "new_class_id": 15,
      "new_class_name": "SD2 A",
      "status": "promoted"
    },
    {
      "student_id": 102,
      "student_name": "Jane Doe",
      "old_grade": "SMP3",
      "old_class_id": 20,
      "old_class_name": "SMP3 A",
      "new_grade": null,
      "new_class_id": null,
      "new_class_name": null,
      "status": "graduated"
    }
  ]
}
```

### API: Confirm Promotion

**Endpoint:** `POST /api/v1/promotions/confirm`

**Request Body:**
```json
{
  "exclude_student_ids": [105, 106] // IDs selected by user to skip
}
```

**Response:**
```json
{
  "id": 12, // The History ID
  "promotion_date": "2026-01-09T10:00:00",
  "status": "applied",
  "summary": {
    "promoted": 43,
    "graduated": 5
  }
}
```

---

## 2. History & Undo

The UI should have a "History" tab showing past bulk promotions.

### API: Get History List

**Endpoint:** `GET /api/v1/promotions/history`

Use this to populate the table of past executions.

**Response:**
```json
[
  {
    "id": 12,
    "promotion_date": "2026-01-09T10:00:00",
    "status": "applied", // "applied" or "reverted"
    "summary": { "promoted": 43, "graduated": 5 },
    "total_affected": 48
  },
  {
    "id": 11,
    "promotion_date": "2025-06-20T09:00:00",
    "status": "reverted",
    "summary": { "promoted": 40 },
    "total_affected": 40
  }
]
```

### API: Get History Detail

**Endpoint:** `GET /api/v1/promotions/history/{id}`

Use this when a user clicks "View Details" on a history row. It allows them to see exactly who was moved.

**Response:**
Same as the Preview response, but wrapped:
```json
{
  "id": 12,
  "promotion_date": "2026-01-09T10:00:00",
  "status": "applied",
  "summary": { "promoted": 43, "graduated": 5 },
  "total_affected": 48,
  "details": [
    // Array of StudentPromotionDetail (same structure as Preview)
  ]
}
```

### API: Undo Promotion

**Endpoint:** `POST /api/v1/promotions/{id}/undo`

Use this when user clicks "Undo" or "Revert" on a history item.
*Note: This reverts the grades and classes to what they were BEFORE that specific promotion event.*

**Response:**
```json
{
  "message": "Promotion undone successfully"
}
```

## Data Types Reference

### Student Promotion Status Types
| Status | Description |
| :--- | :--- |
| `promoted` | Student moved to next grade (e.g., SD1 -> SD2). |
| `graduated` | Student was in final grade (SMP3) and now has no grade. |
| `no_class_available` | System could not find a class for the next grade in the student's region. Action blocked for this student. |
| `error` | Generic error. |

### Grade Progression
The system automatically handles the following mapping:
- TKA -> TKB
- TKB -> SD1
- SD1 -> SD2
- ...
- SD6 -> SMP1
- ...
- SMP3 -> Graduated (None)

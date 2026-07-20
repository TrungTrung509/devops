# Alembic Commands 3 Sites
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
## Nguyên tắc

Mỗi site = 1 database riêng → dùng file `.ini` tương ứng khi chạy lệnh.
## 0. Mỗi khi có Model mới phải import vào FOLDER MODELS

---

## 1. Tạo migration (tự động)

```bash
alembic -c alembic_hadong.ini revision --autogenerate -m "message"
alembic -c alembic_hoalac.ini revision --autogenerate -m "message"
alembic -c alembic_ngoctruc.ini revision --autogenerate -m "message"
```

👉 Ý nghĩa:

* So sánh model với DB
* Tạo file migration (thay đổi schema)
* Message giống kiểu trong commit github
* Ghi message chuẩn để không đè version
---

## 🔼 2. Áp dụng migration (update DB)

```bash
alembic -c alembic_hadong.ini upgrade head
alembic -c alembic_hoalac.ini upgrade head
alembic -c alembic_ngoctruc.ini upgrade head
```

👉 Ý nghĩa:

* Cập nhật database lên version mới nhất
*
---

## 🔽 3. Rollback (quay lại)

```bash
alembic -c alembic_hadong.ini downgrade -1
alembic -c alembic_hoalac.ini downgrade -1
alembic -c alembic_ngoctruc.ini downgrade -1
```

👉 Ý nghĩa:

* Quay lại 1 version trước đó

---

## 📜 4. Xem lịch sử migration

```bash
alembic -c alembic_hadong.ini history
alembic -c alembic_hoalac.ini history
alembic -c alembic_ngoctruc.ini history
```

👉 Ý nghĩa:

* Xem các version đã tạo

---

## 5. Xem version hiện tại

```bash
alembic -c alembic_hadong.ini current
alembic -c alembic_hoalac.ini current
alembic -c alembic_ngoctruc.ini current
```

👉 Ý nghĩa:

* Kiểm tra DB đang ở version nào

---

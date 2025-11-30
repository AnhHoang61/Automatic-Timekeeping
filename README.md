# **Automatic Attendance System – README**

## 📌 **Giới thiệu**

Hệ thống chấm công tự động sử dụng camera IP và công nghệ nhận diện khuôn mặt.
Các thành phần chính:

* **Frontend:** ReactJS
* **Backend:** Python (FastAPI/Flask), OpenCV
* **Face Recognition:** DeepFace (ArcFace)
* **Database:** MySQL
* **Camera:** Imou IPC-A32EP (RTSP)

---

## 🚀 **1. Cài đặt Backend (Python)**

### **Yêu cầu**

* Python 3.8+
* Pip

### **Cài thư viện**

```bash
pip install -r requirements.txt
```

**requirements.txt ví dụ:**

```
opencv-python
deepface
numpy
fastapi
uvicorn
mysql-connector-python
sqlalchemy
python-multipart
```

### **Chạy backend**

Nếu dùng FastAPI:

```bash
uvicorn main:app --reload
```

Backend sẽ chạy tại:

```
http://localhost:8000
```

### **Cấu hình RTSP camera**

Cập nhật URL RTSP trong file cấu hình hoặc biến môi trường:

```
rtsp://username:password@<camera-ip>:554/Streaming/Channels/101
```

---

## 🌐 **2. Cài đặt Frontend (ReactJS)**

### **Yêu cầu**

* NodeJS 16+
* npm 

### **Cài thư viện**

```bash
npm install
```

### **Chạy frontend**

```bash
npm start
```

Frontend chạy tại:

```
http://localhost:3000
```

---

## 🗄️ **3. Cấu hình MySQL Database**

### **Tạo database**

```sql
CREATE DATABASE attendance_system;
```

### **Tạo các bảng chính**

```sql
CREATE TABLE employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    position VARCHAR(100),
    image VARCHAR(255)
);

CREATE TABLE face_embeddings (
    embedding_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT,
    embedding LONGTEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE attendance_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT,
    timestamp DATETIME,
    type VARCHAR(20),
    captured_image VARCHAR(255),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);


### **Cấu hình kết nối MySQL trong backend**

```python
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "your_password"
DB_NAME = "attendance_system"
```

---

## 🧪 **4. Chạy thử hệ thống**

1. Bật camera IP và kiểm tra luồng RTSP hoạt động.
2. Chạy backend Python để xử lý nhận diện khuôn mặt.
3. Chạy frontend ReactJS để xem dữ liệu và bảng chấm công.
4. Khi nhân viên đi qua camera → hệ thống tự động nhận diện và ghi log vào MySQL.

---

## 📷 **5. Công nghệ sử dụng**

* **DeepFace (ArcFace)** – nhận diện khuôn mặt
* **OpenCV** – đọc luồng RTSP
* **FastAPI/Flask** – backend API
* **ReactJS** – website quản trị
* **MySQL** – lưu dữ liệu chấm công
* **Camera Imou IPC-A32EP** – đầu vào hình ảnh

---


# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import date, datetime, timedelta
from uuid import uuid4   # dùng uuid4() để tạo tên file ảnh
import os
import json
import numpy as np

from deepface import DeepFace # dùng nhận diện khuôn mặt
from openpyxl.workbook import Workbook

# Import database helper của bạn
from db import fetch_all, fetch_one, execute

from io import BytesIO
from flask import send_file

# -----------------------------
# KHỞI TẠO APP
# -----------------------------
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

# -----------------------------
# CẤU HÌNH CORS CHO FRONTEND REACT (VITE)
# -----------------------------
CORS(
    app,
    resources={r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174"
        ]
    }},
    supports_credentials=True,
)

def parse_date(s, default=None):
    if not s:
        return default
    return datetime.strptime(s, "%Y-%m-%d").date()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_embedding(image_path: str):
    """
    Dùng DeepFace để sinh face embedding cho 1 ảnh.
    Trả về list float (embedding) hoặc None nếu không tìm thấy mặt.
    """
    try:
        reps = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet512",   # hoặc "ArcFace"
            enforce_detection=True
        )

        # TH1: list các khuôn mặt
        if isinstance(reps, list) and len(reps) > 0:
            return reps[0]["embedding"]

        # TH2: 1 dict
        if isinstance(reps, dict) and "embedding" in reps:
            return reps["embedding"]

        return None
    except Exception as e:
        print("Lỗi DeepFace.represent:", e)
        return None


# def extract_embedding(image_path: str):
#     """
#     Dùng DeepFace để sinh face embedding cho 1 ảnh.
#     Trả về list float (embedding) hoặc None nếu không tìm thấy mặt.
#     """
#     try:
#         reps = DeepFace.represent(
#             img_path=image_path,
#             model_name="Facenet512",   # hoặc "ArcFace" nếu bạn đã dùng trước đó
#             enforce_detection=True
#         )
#         # DeepFace.represent trả về list các khuôn mặt, mình lấy cái đầu
#         if isinstance(reps, list) and len(reps) > 0:
#             return reps[0]["embedding"]
#         return None
#     except Exception as e:
#         print("Lỗi DeepFace.represent:", e)
#         return None

# def cosine_distance(v1, v2):
#     v1 = np.array(v1, dtype=np.float32)
#     v2 = np.array(v2, dtype=np.float32)
#     dot = np.dot(v1, v2)
#     norm1 = np.linalg.norm(v1)
#     norm2 = np.linalg.norm(v2)
#     if norm1 == 0 or norm2 == 0:
#         return 1.0
#     return 1 - (dot / (norm1 * norm2))

def identify_employee_by_embedding(embedding, threshold=0.4):
    """
    Tìm nhân viên có face_embedding gần nhất.
    Giả sử bảng employees có cột face_embedding (JSON) như bạn đang dùng.
    Trả về dict employee hoặc None nếu không match.
    """
    # Lấy tất cả nhân viên có embedding
    rows = fetch_all("""
        SELECT employee_id, fullname, department, position, face_embedding
        FROM employees
        WHERE face_embedding IS NOT NULL
    """)

    best_emp = None
    best_dist = 999.0

    for row in rows:
        try:
            stored = json.loads(row["face_embedding"])
        except Exception:
            continue

        dist = cosine_distance(embedding, stored)
        if dist < best_dist:
            best_dist = dist
            best_emp = row

    if best_emp is None or best_dist > threshold:
        return None, best_dist

    return best_emp, best_dist

def cosine_distance(vec1, vec2) -> float:
    """Khoảng cách cosine: càng nhỏ thì càng giống nhau."""
    a = np.array(vec1)
    b = np.array(vec2)
    # tránh chia cho 0
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 1.0
    return 1.0 - float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    """Trả về dữ liệu tổng quan cho Dashboard"""

    # ?date=2025-11-26 (nếu không truyền -> hôm nay)
    date_str = request.args.get("date")
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400
    else:
        target_date = date.today()

    # --------- SUMMARY ---------
    # Tổng nhân viên
    total_employees_row = fetch_one(
        "SELECT COUNT(*) AS total FROM employees"
    )
    total_employees = total_employees_row["total"]

    # Đã check-in trong ngày
    checked_in_row = fetch_one(
        """
        SELECT COUNT(DISTINCT employee_id) AS total
        FROM attendance_logs
        WHERE date = %s AND check_in IS NOT NULL
        """,
        (target_date,),
    )
    checked_in_today = checked_in_row["total"]

    # Đang làm việc (đã in, chưa out)
    working_row = fetch_one(
        """
        SELECT COUNT(DISTINCT employee_id) AS total
        FROM attendance_logs
        WHERE date = %s AND check_in IS NOT NULL AND check_out IS NULL
        """,
        (target_date,),
    )
    working_now = working_row["total"]

    # Đi trễ (status = 'LATE')
    late_row = fetch_one(
        """
        SELECT COUNT(*) AS total
        FROM attendance_logs
        WHERE date = %s AND status = 'LATE'
        """,
        (target_date,),
    )
    late_count = late_row["total"]

    # --------- BẢNG CHẤM CÔNG HÔM NAY ---------
    today_logs = fetch_all(
        """
        SELECT 
            al.log_id,
            al.date,
            al.check_in,
            al.check_out,
            al.status,
            e.employee_id,
            e.fullname,
            e.department,
            s.shift_name
        FROM attendance_logs al
        JOIN employees e ON e.employee_id = al.employee_id
        JOIN shifts s ON s.shift_id = al.shift_id
        WHERE al.date = %s
        ORDER BY al.check_in ASC
        """,
        (target_date,),
    )

    # --------- TOP ĐI TRỄ TRONG THÁNG ---------
    first_day = target_date.replace(day=1)
    if target_date.month == 12:
        next_month = target_date.replace(year=target_date.year + 1, month=1, day=1)
    else:
        next_month = target_date.replace(month=target_date.month + 1, day=1)

    top_late = fetch_all(
        """
        SELECT 
            e.employee_id,
            e.fullname,
            e.department,
            COUNT(*) AS late_count
        FROM attendance_logs al
        JOIN employees e ON e.employee_id = al.employee_id
        WHERE al.status = 'LATE'
          AND al.date >= %s
          AND al.date < %s
        GROUP BY e.employee_id, e.fullname, e.department
        ORDER BY late_count DESC
        LIMIT 5
        """,
        (first_day, next_month),
    )

    return jsonify(
        {
            "summary": {
                "date": target_date.isoformat(),
                "total_employees": total_employees,
                "checked_in_today": checked_in_today,
                "working_now": working_now,
                "late_count": late_count,
            },
            "today_logs": today_logs,
            "top_late": top_late,
        }
    )


# ========== HEALTH CHECK ==========
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


# ========== EMPLOYEES CRUD ==========

# Lấy danh sách tất cả nhân viên
@app.route("/api/employees", methods=["GET"])
def get_employees():
    query = "SELECT * FROM employees ORDER BY employee_id DESC"
    rows = fetch_all(query)
    return jsonify(rows)


# Lấy thông tin 1 nhân viên theo id
@app.route("/api/employees/<int:employee_id>", methods=["GET"])
def get_employee(employee_id):
    query = "SELECT * FROM employees WHERE employee_id = %s"
    row = fetch_one(query, (employee_id,))
    if row is None:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(row)


# Thêm mới nhân viên
@app.route("/api/employees", methods=["POST"])
def create_employee():
    data = request.json

    query = """
        INSERT INTO employees (fullname, gender, dob, department, position,
                               phone, email, avatar, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
    """
    params = (
        data.get("fullname"),
        data.get("gender"),
        data.get("dob"),
        data.get("department"),
        data.get("position"),
        data.get("phone"),
        data.get("email"),
        data.get("avatar"),
    )
    new_id = execute(query, params)
    return jsonify({"employee_id": new_id}), 201


# Cập nhật thông tin nhân viên
@app.route("/api/employees/<int:employee_id>", methods=["PUT"])
def update_employee(employee_id):
    data = request.json

    query = """
        UPDATE employees
        SET fullname=%s,
            gender=%s,
            dob=%s,
            department=%s,
            position=%s,
            phone=%s,
            email=%s,
            avatar=%s,
            updated_at=NOW()
        WHERE employee_id=%s
    """
    params = (
        data.get("fullname"),
        data.get("gender"),
        data.get("dob"),
        data.get("department"),
        data.get("position"),
        data.get("phone"),
        data.get("email"),
        data.get("avatar"),
        employee_id,
    )
    execute(query, params)
    return jsonify({"message": "Employee updated"})


# Xóa nhân viên
@app.route("/api/employees/<int:employee_id>", methods=["DELETE"])
def delete_employee(employee_id):
    query = "DELETE FROM employees WHERE employee_id = %s"
    execute(query, (employee_id,))
    return jsonify({"message": "Employee deleted"})
# ========== FACE ENROLLMENT (UPLOAD ẢNH + LƯU EMBEDDING) ==========

@app.route("/api/employees/<int:employee_id>/face", methods=["POST"])
def upload_employee_face(employee_id):
    """
    Nhận ảnh khuôn mặt của nhân viên, sinh embedding bằng DeepFace
    và lưu vào cột face_embedding trong bảng employees.
    """

    # 1. Kiểm tra xem nhân viên có tồn tại không
    emp = fetch_one("SELECT employee_id FROM employees WHERE employee_id = %s", (employee_id,))
    if emp is None:
        return jsonify({"error": "Employee not found"}), 404

    # 2. Kiểm tra file trong request
    if "image" not in request.files:
        return jsonify({"error": "No file part 'image' in request"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Use jpg, jpeg, png"}), 400

    # 3. Lưu file tạm
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{employee_id}_{uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # 4. Gọi DeepFace để sinh embedding
    try:
        reps = DeepFace.represent(
            img_path=file_path,
            model_name="Facenet512",    # hoặc 'Facenet', 'ArcFace' tùy bạn
            detector_backend="opencv"   # hoặc 'retinaface', 'mtcnn'...
        )
        # DeepFace.represent trả về list, lấy phần tử đầu
        embedding = reps[0]["embedding"]
    except Exception as e:
        # Nếu không detect được mặt thì xóa file và báo lỗi
        try:
            os.remove(file_path)
        except Exception:
            pass
        return jsonify({"error": "Could not extract face embedding", "detail": str(e)}), 400

    # 5. Lưu embedding (dưới dạng JSON string) vào DB
    embedding_str = json.dumps(embedding)

    execute(
        "UPDATE employees SET face_embedding = %s WHERE employee_id = %s",
        (embedding_str, employee_id),
    )

    # (tuỳ chọn) update luôn cột avatar là tên file
    # execute("UPDATE employees SET avatar = %s WHERE employee_id = %s", (filename, employee_id))

    return jsonify({
        "message": "Đã lưu khuôn mặt thành công",
        "employee_id": employee_id,
        "embedding_dim": len(embedding)
    }), 200

#========== FACE RECOGNITION (NHẬN DIỆN KHUÔN MẶT) ==========

@app.route("/api/face/identify", methods=["POST"])
def identify_face():
    """
    Nhận ảnh khuôn mặt, so sánh với các embedding đã lưu,
    trả về nhân viên giống nhất (nếu đủ ngưỡng).
    """

    # 1. Lấy file từ request
    if "image" not in request.files:
        return jsonify({"error": "No file part 'image' in request"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Use jpg, jpeg, png"}), 400

    # 2. Lưu file tạm
    ext = file.filename.rsplit(".", 1)[1].lower()
    temp_name = f"identify_{uuid4().hex}.{ext}"
    temp_path = os.path.join(UPLOAD_FOLDER, temp_name)
    file.save(temp_path)

    try:
        # 3. Sinh embedding của ảnh gửi lên (dùng helper)
        query_emb = extract_embedding(temp_path)
    finally:
        # luôn cố gắng xóa file tạm, kể cả khi lỗi
        try:
            os.remove(temp_path)
        except Exception:
            pass

    if query_emb is None:
        return jsonify({
            "matched": False,
            "message": "Could not extract embedding from image"
        }), 400

    # 4. Tìm nhân viên giống nhất (dùng helper)
    THRESHOLD = 0.4  # giữ nguyên ngưỡng bạn đang dùng
    best_employee, best_distance = identify_employee_by_embedding(
        query_emb, threshold=THRESHOLD
    )

    # Không tìm được ai đủ giống
    if best_employee is None:
        return jsonify({
            "matched": False,
            "message": "No matching employee found",
            "best_distance": best_distance
        }), 200

    # 5. Thành công
    return jsonify({
        "matched": True,
        "employee_id": best_employee["employee_id"],
        "fullname": best_employee["fullname"],
        "distance": best_distance
    }), 200


@app.route("/api/face/checkin", methods=["POST"])
def face_checkin():
    # 1. Lấy file ảnh + shift_id từ form-data
    if "image" not in request.files:
        return jsonify({"error": "image is required"}), 400

    file = request.files["image"]
    shift_id = request.form.get("shift_id", type=int)

    if not shift_id:
        return jsonify({"error": "shift_id is required"}), 400

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Use jpg, jpeg, png"}), 400

    # 2. Lưu file tạm
    ext = file.filename.rsplit(".", 1)[1].lower()
    temp_name = f"checkin_{uuid4().hex}.{ext}"
    temp_path = os.path.join(UPLOAD_FOLDER, temp_name)
    file.save(temp_path)

    # 3. Sinh embedding của ảnh gửi lên
    try:
        reps = DeepFace.represent(
            img_path=temp_path,
            model_name="Facenet512",
            detector_backend="opencv"
        )
        query_emb = reps[0]["embedding"]
    except Exception as e:
        os.remove(temp_path)
        return jsonify({"error": "Could not extract embedding", "detail": str(e)}), 400

    # 4. So sánh với embedding trong DB (giống /api/face/identify)
    rows = fetch_all(
        "SELECT employee_id, fullname, face_embedding FROM employees WHERE face_embedding IS NOT NULL"
    )

    if not rows:
        os.remove(temp_path)
        return jsonify({"error": "No enrolled faces in database"}), 400

    best_employee = None
    best_distance = 1.0

    for row in rows:
        try:
            emb = json.loads(row["face_embedding"])
        except Exception:
            continue

        dist = cosine_distance(query_emb, emb)
        if dist < best_distance:
            best_distance = dist
            best_employee = row

    os.remove(temp_path)

    THRESHOLD = 0.4
    if best_employee is None or best_distance > THRESHOLD:
        return jsonify({
            "matched": False,
            "message": "No matching employee found",
            "best_distance": best_distance
        }), 200

    employee_id = best_employee["employee_id"]

    # 5. Từ đây trở đi: logic CHECK-IN giống /api/attendance/checkin
    today = date.today()
    now = datetime.now()

    # tìm log hôm nay của nhân viên + ca đó
    existing = fetch_one(
        """
        SELECT * FROM attendance_logs
        WHERE employee_id = %s AND shift_id = %s AND date = %s
        """,
        (employee_id, shift_id, today),
    )

    if existing and existing["check_in"] is not None:
        return jsonify({"error": "Employee already checked in"}), 400

    if existing:
        # đã có record -> cập nhật giờ check_in
        execute(
            "UPDATE attendance_logs SET check_in = %s, status = %s WHERE log_id = %s",
            (now, "PRESENT", existing["log_id"]),
        )
        log_id = existing["log_id"]
    else:
        # chưa có record -> tạo mới
        log_id = execute(
            """
            INSERT INTO attendance_logs (employee_id, shift_id, date, check_in, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (employee_id, shift_id, today, now, "PRESENT"),
        )

    return jsonify({
        "matched": True,
        "employee_id": employee_id,
        "fullname": best_employee["fullname"],
        "distance": best_distance,
        "log_id": log_id,
        "message": "Face check-in success"
    }), 200

@app.route("/api/face/checkout", methods=["POST"])
def face_checkout():
    if "image" not in request.files:
        return jsonify({"error": "image is required"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Use jpg, jpeg, png"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    temp_name = f"checkout_{uuid4().hex}.{ext}"
    temp_path = os.path.join(UPLOAD_FOLDER, temp_name)
    file.save(temp_path)

    try:
        reps = DeepFace.represent(
            img_path=temp_path,
            model_name="Facenet512",
            detector_backend="opencv"
        )
        query_emb = reps[0]["embedding"]
    except Exception as e:
        os.remove(temp_path)
        return jsonify({"error": "Could not extract embedding", "detail": str(e)}), 400

    rows = fetch_all(
        "SELECT employee_id, fullname, face_embedding FROM employees WHERE face_embedding IS NOT NULL"
    )

    if not rows:
        os.remove(temp_path)
        return jsonify({"error": "No enrolled faces in database"}), 400

    best_employee = None
    best_distance = 1.0

    for row in rows:
        try:
            emb = json.loads(row["face_embedding"])
        except Exception:
            continue

        dist = cosine_distance(query_emb, emb)
        if dist < best_distance:
            best_distance = dist
            best_employee = row

    os.remove(temp_path)

    THRESHOLD = 0.4
    if best_employee is None or best_distance > THRESHOLD:
        return jsonify({
            "matched": False,
            "message": "No matching employee found",
            "best_distance": best_distance
        }), 200

    employee_id = best_employee["employee_id"]

    # ----- Logic CHECK-OUT giống /api/attendance/checkout -----
    today = date.today()
    now = datetime.now()

    existing = fetch_one(
        """
        SELECT * FROM attendance_logs
        WHERE employee_id = %s AND date = %s
        ORDER BY log_id DESC LIMIT 1
        """,
        (employee_id, today),
    )

    if existing is None:
        return jsonify({"error": "No attendance record for today"}), 400

    if existing["check_in"] is None:
        return jsonify({"error": "Employee has not checked in yet"}), 400

    if existing["check_out"] is not None:
        return jsonify({"error": "Employee already checked out"}), 400

    execute(
        "UPDATE attendance_logs SET check_out = %s WHERE log_id = %s",
        (now, existing["log_id"]),
    )

    return jsonify({
        "matched": True,
        "employee_id": employee_id,
        "fullname": best_employee["fullname"],
        "distance": best_distance,
        "log_id": existing["log_id"],
        "message": "Face check-out success"
    }), 200


# ========== SHIFTS CRUD ==========

# Lấy tất cả ca làm
@app.route("/api/shifts", methods=["GET"])
def get_shifts():
    rows = fetch_all("SELECT * FROM shifts ORDER BY shift_id ASC")
    return jsonify(rows)


# Lấy 1 ca làm
@app.route("/api/shifts/<int:shift_id>", methods=["GET"])
def get_shift(shift_id):
    row = fetch_one("SELECT * FROM shifts WHERE shift_id = %s", (shift_id,))
    if row is None:
        return jsonify({"error": "Shift not found"}), 404
    return jsonify(row)


# Thêm ca làm mới
@app.route("/api/shifts", methods=["POST"])
def create_shift():
    data = request.json

    query = """
        INSERT INTO shifts (shift_name, start_time, end_time, late_limit, early_limit)
        VALUES (%s, %s, %s, %s, %s)
    """
    params = (
        data.get("shift_name"),
        data.get("start_time"),   # "HH:MM:SS"
        data.get("end_time"),     # "HH:MM:SS"
        data.get("late_limit"),
        data.get("early_limit"),
    )
    new_id = execute(query, params)
    return jsonify({"shift_id": new_id}), 201


# Cập nhật ca làm
@app.route("/api/shifts/<int:shift_id>", methods=["PUT"])
def update_shift(shift_id):
    data = request.json

    query = """
        UPDATE shifts
        SET shift_name=%s,
            start_time=%s,
            end_time=%s,
            late_limit=%s,
            early_limit=%s
        WHERE shift_id=%s
    """
    params = (
        data.get("shift_name"),
        data.get("start_time"),
        data.get("end_time"),
        data.get("late_limit"),
        data.get("early_limit"),
        shift_id,
    )
    execute(query, params)
    return jsonify({"message": "Shift updated"})


# Xóa ca làm
@app.route("/api/shifts/<int:shift_id>", methods=["DELETE"])
def delete_shift(shift_id):
    query = "DELETE FROM shifts WHERE shift_id = %s"
    execute(query, (shift_id,))
    return jsonify({"message": "Shift deleted"})

# ========== EMPLOYEES_SHIFTS (PHÂN CA) ==========

# Xem tất cả ca hiện tại của 1 nhân viên
@app.route("/api/employees/<int:employee_id>/shifts", methods=["GET"])
def get_employee_shifts(employee_id):
    query = """
        SELECT es.id, es.employee_id, es.shift_id,
               es.effective_from, es.effective_to,
               s.shift_name, s.start_time, s.end_time
        FROM employees_shifts es
        JOIN shifts s ON es.shift_id = s.shift_id
        WHERE es.employee_id = %s
        ORDER BY es.effective_from DESC
    """
    rows = fetch_all(query, (employee_id,))
    return jsonify(rows)


# Gán 1 ca cho nhân viên
@app.route("/api/employees/<int:employee_id>/shifts", methods=["POST"])
def assign_shift_to_employee(employee_id):
    data = request.json

    query = """
        INSERT INTO employees_shifts (employee_id, shift_id, effective_from, effective_to)
        VALUES (%s, %s, %s, %s)
    """
    params = (
        employee_id,
        data.get("shift_id"),
        data.get("effective_from"),   # "YYYY-MM-DD"
        data.get("effective_to"),     # có thể là null
    )
    new_id = execute(query, params)
    return jsonify({"id": new_id}), 201


# Cập nhật khoảng hiệu lực phân ca
@app.route("/api/employees_shifts/<int:es_id>", methods=["PUT"])
def update_employee_shift(es_id):
    data = request.json

    query = """
        UPDATE employees_shifts
        SET shift_id=%s,
            effective_from=%s,
            effective_to=%s
        WHERE id=%s
    """
    params = (
        data.get("shift_id"),
        data.get("effective_from"),
        data.get("effective_to"),
        es_id,
    )
    execute(query, params)
    return jsonify({"message": "Employee shift updated"})


# Xóa phân ca
@app.route("/api/employees_shifts/<int:es_id>", methods=["DELETE"])
def delete_employee_shift(es_id):
    query = "DELETE FROM employees_shifts WHERE id = %s"
    execute(query, (es_id,))
    return jsonify({"message": "Employee shift deleted"})


# ========== ATTENDANCE CHECKIN / CHECKOUT ==========

# Lấy chấm công hôm nay
@app.route("/api/attendance/today", methods=["GET"])
def get_attendance_today():
    today = date.today()
    query = """
        SELECT al.*, e.fullname, e.department, s.shift_name
        FROM attendance_logs al
        JOIN employees e ON al.employee_id = e.employee_id
        JOIN shifts s ON al.shift_id = s.shift_id
        WHERE al.date = %s
        ORDER BY al.check_in ASC
    """
    rows = fetch_all(query, (today,))
    return jsonify(rows)


# Lấy lịch sử chấm công của 1 nhân viên
@app.route("/api/attendance/employee/<int:employee_id>", methods=["GET"])
def get_attendance_by_employee(employee_id):
    query = """
        SELECT al.*, s.shift_name
        FROM attendance_logs al
        JOIN shifts s ON al.shift_id = s.shift_id
        WHERE al.employee_id = %s
        ORDER BY al.date DESC
    """
    rows = fetch_all(query, (employee_id,))
    return jsonify(rows)

# Check-in
@app.route("/api/attendance/checkin", methods=["POST"])
def attendance_checkin():
    data = request.json
    employee_id = data.get("employee_id")
    shift_id = data.get("shift_id")
    today = date.today()
    now = datetime.now()

    if not employee_id or not shift_id:
        return jsonify({"error": "employee_id and shift_id are required"}), 400

    # Tìm bản ghi chấm công hôm nay cho nhân viên + ca đó
    existing = fetch_one(
        """
        SELECT * FROM attendance_logs
        WHERE employee_id = %s AND shift_id = %s AND date = %s
        """,
        (employee_id, shift_id, today),
    )

    if existing and existing["check_in"] is not None:
        return jsonify({"error": "Employee already checked in"}), 400

    if existing:
        # Đã có record, chỉ cập nhật giờ check_in
        execute(
            "UPDATE attendance_logs SET check_in = %s, status = %s WHERE log_id = %s",
            (now, "PRESENT", existing["log_id"]),
        )
        log_id = existing["log_id"]
    else:
        # Tạo bản ghi mới
        log_id = execute(
            """
            INSERT INTO attendance_logs (employee_id, shift_id, date, check_in, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (employee_id, shift_id, today, now, "PRESENT"),
        )

    return jsonify({"message": "Check-in success", "log_id": log_id})


# Check-out
@app.route("/api/attendance/checkout", methods=["POST"])
def attendance_checkout():
    data = request.json
    employee_id = data.get("employee_id")
    shift_id = data.get("shift_id")
    today = date.today()
    now = datetime.now()

    if not employee_id or not shift_id:
        return jsonify({"error": "employee_id and shift_id are required"}), 400

    existing = fetch_one(
        """
        SELECT * FROM attendance_logs
        WHERE employee_id = %s AND shift_id = %s AND date = %s
        """,
        (employee_id, shift_id, today),
    )

    if not existing or existing["check_in"] is None:
        return jsonify({"error": "No check-in record for today"}), 400

    if existing["check_out"] is not None:
        return jsonify({"error": "Employee already checked out"}), 400

    execute(
        "UPDATE attendance_logs SET check_out = %s WHERE log_id = %s",
        (now, existing["log_id"]),
    )

    return jsonify({"message": "Check-out success", "log_id": existing["log_id"]})

#Reports

@app.route("/api/reports/summary", methods=["GET"])
def report_summary():
    """
    Tổng hợp báo cáo trong khoảng from_date - to_date
    param:
      from: YYYY-MM-DD
      to:   YYYY-MM-DD
      department: optional, lọc theo phòng ban
    """

    from_str = request.args.get("from")
    to_str = request.args.get("to")
    dept = request.args.get("department")  # có thể là None hoặc "Tất cả"

    today = date.today()
    from_date = parse_date(from_str, default=today.replace(day=1))
    to_date   = parse_date(to_str,   default=today)

    if from_date > to_date:
        return jsonify({"error": "from must <= to"}), 400

    # số ngày trong khoảng (bao gồm cả 2 đầu)
    working_days = (to_date - from_date).days + 1

    # Tổng nhân viên (có thể lọc theo department)
    if dept and dept.lower() != "tất cả":
        row_emp = fetch_one(
            "SELECT COUNT(*) AS total FROM employees WHERE department = %s",
            (dept,),
        )
    else:
        row_emp = fetch_one("SELECT COUNT(*) AS total FROM employees")
    total_employees = row_emp["total"] or 0

    # Tổng số record trong attendance_logs trong khoảng
    # (chỉ tính có check_in, coi là đi làm)
    if dept and dept.lower() != "tất cả":
        present_row = fetch_one(
            """
            SELECT COUNT(DISTINCT al.employee_id, al.date) AS present_days
            FROM attendance_logs al
            JOIN employees e ON e.employee_id = al.employee_id
            WHERE al.date BETWEEN %s AND %s
              AND al.check_in IS NOT NULL
              AND e.department = %s
            """,
            (from_date, to_date, dept),
        )
    else:
        present_row = fetch_one(
            """
            SELECT COUNT(DISTINCT employee_id, date) AS present_days
            FROM attendance_logs
            WHERE date BETWEEN %s AND %s
              AND check_in IS NOT NULL
            """,
            (from_date, to_date),
        )
    present_days = present_row["present_days"] or 0

    # đi trễ
    if dept and dept.lower() != "tất cả":
        late_row = fetch_one(
            """
            SELECT COUNT(*) AS late_count
            FROM attendance_logs al
            JOIN employees e ON e.employee_id = al.employee_id
            WHERE al.date BETWEEN %s AND %s
              AND al.status = 'LATE'
              AND e.department = %s
            """,
            (from_date, to_date, dept),
        )
    else:
        late_row = fetch_one(
            """
            SELECT COUNT(*) AS late_count
            FROM attendance_logs
            WHERE date BETWEEN %s AND %s
              AND status = 'LATE'
            """,
            (from_date, to_date),
        )
    late_count = late_row["late_count"] or 0

    # Tổng giờ công: tính (check_out - check_in) theo giờ
    if dept and dept.lower() != "tất cả":
        rows_hours = fetch_all(
            """
            SELECT al.check_in, al.check_out
            FROM attendance_logs al
            JOIN employees e ON e.employee_id = al.employee_id
            WHERE al.date BETWEEN %s AND %s
              AND al.check_in IS NOT NULL
              AND al.check_out IS NOT NULL
              AND e.department = %s
            """,
            (from_date, to_date, dept),
        )
    else:
        rows_hours = fetch_all(
            """
            SELECT check_in, check_out
            FROM attendance_logs
            WHERE date BETWEEN %s AND %s
              AND check_in IS NOT NULL
              AND check_out IS NOT NULL
            """,
            (from_date, to_date),
        )

    total_hours = 0.0
    for r in rows_hours:
        ci = r["check_in"]
        co = r["check_out"]
        delta = co - ci
        total_hours += delta.total_seconds() / 3600.0

    # ngày vắng = (số ngày * số nhân viên) - số ngày đi làm
    total_slots = working_days * total_employees
    absent_days = max(total_slots - present_days, 0)

    return jsonify({
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
        "working_days": working_days,
        "total_employees": total_employees,
        "total_hours": round(total_hours, 2),
        "late_count": int(late_count),
        "absent_days": int(absent_days),
    })

@app.route("/api/reports/by-day", methods=["GET"])
def report_by_day():
    from_date = parse_date(request.args.get("from"))
    to_date   = parse_date(request.args.get("to"))
    dept      = request.args.get("department")

    if from_date is None or to_date is None:
        return jsonify({"error": "from & to are required (YYYY-MM-DD)"}), 400

    if from_date > to_date:
        return jsonify({"error": "from must <= to"}), 400

    # tổng nhân viên dùng cho tính vắng
    if dept and dept.lower() != "tất cả":
        row_emp = fetch_one(
            "SELECT COUNT(*) AS total FROM employees WHERE department = %s",
            (dept,),
        )
    else:
        row_emp = fetch_one("SELECT COUNT(*) AS total FROM employees")
    total_employees = row_emp["total"] or 0

    if dept and dept.lower() != "tất cả":
        rows = fetch_all(
            """
            SELECT al.date,
                   COUNT(DISTINCT CASE WHEN al.check_in IS NOT NULL THEN al.employee_id END) AS present,
                   SUM(CASE WHEN al.status = 'LATE' THEN 1 ELSE 0 END) AS late
            FROM attendance_logs al
            JOIN employees e ON e.employee_id = al.employee_id
            WHERE al.date BETWEEN %s AND %s
              AND e.department = %s
            GROUP BY al.date
            ORDER BY al.date
            """,
            (from_date, to_date, dept),
        )
    else:
        rows = fetch_all(
            """
            SELECT date,
                   COUNT(DISTINCT CASE WHEN check_in IS NOT NULL THEN employee_id END) AS present,
                   SUM(CASE WHEN status = 'LATE' THEN 1 ELSE 0 END) AS late
            FROM attendance_logs
            WHERE date BETWEEN %s AND %s
            GROUP BY date
            ORDER BY date
            """,
            (from_date, to_date),
        )

    # build dict theo ngày
    data_map = {r["date"]: r for r in rows}

    result = []
    d = from_date
    while d <= to_date:
        r = data_map.get(d, None)
        present = r["present"] if r else 0
        late    = r["late"] if r else 0
        absent  = max(total_employees - present, 0)

        result.append({
            "date": d.isoformat(),
            "total_employees": total_employees,
            "present": int(present),
            "late": int(late),
            "absent": int(absent),
        })

        d += timedelta(days=1)

    return jsonify(result)

@app.route("/api/reports/by-employee", methods=["GET"])
def report_by_employee():
    from_date = parse_date(request.args.get("from"))
    to_date   = parse_date(request.args.get("to"))
    dept      = request.args.get("department")

    if from_date is None or to_date is None:
        return jsonify({"error": "from & to are required"}), 400
    if from_date > to_date:
        return jsonify({"error": "from must <= to"}), 400

    working_days = (to_date - from_date).days + 1

    if dept and dept.lower() != "tất cả":
        rows = fetch_all(
            """
            SELECT e.employee_id,
                   e.fullname,
                   e.department,
                   COUNT(DISTINCT CASE WHEN al.check_in IS NOT NULL THEN al.date END) AS present_days,
                   SUM(CASE WHEN al.status = 'LATE' THEN 1 ELSE 0 END) AS late_days
            FROM employees e
            LEFT JOIN attendance_logs al
              ON e.employee_id = al.employee_id
             AND al.date BETWEEN %s AND %s
            WHERE e.department = %s
            GROUP BY e.employee_id, e.fullname, e.department
            ORDER BY e.fullname
            """,
            (from_date, to_date, dept),
        )
    else:
        rows = fetch_all(
            """
            SELECT e.employee_id,
                   e.fullname,
                   e.department,
                   COUNT(DISTINCT CASE WHEN al.check_in IS NOT NULL THEN al.date END) AS present_days,
                   SUM(CASE WHEN al.status = 'LATE' THEN 1 ELSE 0 END) AS late_days
            FROM employees e
            LEFT JOIN attendance_logs al
              ON e.employee_id = al.employee_id
             AND al.date BETWEEN %s AND %s
            GROUP BY e.employee_id, e.fullname, e.department
            ORDER BY e.fullname
            """,
            (from_date, to_date),
        )

    result = []
    for r in rows:
        present = r["present_days"] or 0
        late    = r["late_days"] or 0
        absent  = max(working_days - present, 0)
        result.append({
            "employee_id": r["employee_id"],
            "fullname": r["fullname"],
            "department": r["department"],
            "working_days": working_days,
            "present_days": int(present),
            "late_days": int(late),
            "absent_days": int(absent),
        })

    return jsonify(result)

@app.route("/api/reports/export", methods=["GET"])
def export_reports_excel():
    from_date = parse_date(request.args.get("from"))
    to_date   = parse_date(request.args.get("to"))
    dept      = request.args.get("department")

    if from_date is None or to_date is None:
        return jsonify({"error": "from & to are required"}), 400
    if from_date > to_date:
        return jsonify({"error": "from must <= to"}), 400

    # lấy lại dữ liệu từ 2 API kia (hoặc gọi lại function bên trên)
    # ở đây đơn giản gọi trực tiếp SQL giống /by-day và /by-employee
    # (để không lặp lại code quá dài, ta gọi lại endpoint nội bộ cho nhanh)

    with app.test_request_context():
        # fake request.args cho by-day
        with app.test_request_context(
            f"/api/reports/by-day?from={from_date}&to={to_date}&department={dept or ''}"
        ):
            by_day_resp = report_by_day()
            by_day_data = by_day_resp.get_json()

        with app.test_request_context(
            f"/api/reports/by-employee?from={from_date}&to={to_date}&department={dept or ''}"
        ):
            by_emp_resp = report_by_employee()
            by_emp_data = by_emp_resp.get_json()

    wb = Workbook()
    ws1 = wb.active
    ws1.title = "By Day"

    ws1.append(["Ngày", "Tổng NV", "Đã đi làm", "Đi trễ", "Vắng"])
    for row in by_day_data:
        ws1.append([
            row["date"],
            row["total_employees"],
            row["present"],
            row["late"],
            row["absent"],
        ])

    ws2 = wb.create_sheet("By Employee")
    ws2.append(["Mã NV", "Họ tên", "Phòng ban",
                "Ngày công", "Đi trễ", "Vắng"])
    for r in by_emp_data:
        ws2.append([
            r["employee_id"],
            r["fullname"],
            r["department"],
            r["present_days"],
            r["late_days"],
            r["absent_days"],
        ])

    # ghi ra buffer
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"report_{from_date}_{to_date}.xlsx"
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )

if __name__ == "__main__":
    app.run(debug=True, port=5000)

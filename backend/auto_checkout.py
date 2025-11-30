import cv2
import requests
import time

# ================== CẤU HÌNH ==================

# Địa chỉ API Flask của bạn
API_BASE = "http://127.0.0.1:5000"

# RTSP URL của camera
RTSP_URL = "rtsp://admin:admin123@192.168.1.6:554/cam/realmonitor?channel=1&subtype=0"

# Chế độ chấm công: "checkin" hoặc "checkout"
MODE = "checkout"          # đổi thành "checkout" khi cần

# Ca làm việc dùng cho check-in (phải trùng shift_id trong DB)
SHIFT_ID = 1

# Khoảng thời gian giữa 2 lần gửi ảnh (giây)
CAPTURE_INTERVAL = 3.0

# Thời gian cooldown (không chấm công lại cùng 1 nhân viên quá nhanh), giây
COOLDOWN_SECONDS = 60


# ================== HÀM GỬI FRAME LÊN API ==================

def send_frame_to_api(frame):
    """
    Encode frame thành JPEG và gửi lên API face_checkin / face_checkout.
    Trả về JSON response (dict) hoặc None nếu lỗi.
    """
    # Encode frame -> jpg bytes
    ret, jpeg = cv2.imencode(".jpg", frame)
    if not ret:
        print("[ERROR] Không encode được frame thành JPEG")
        return None

    files = {
        "image": ("frame.jpg", jpeg.tobytes(), "image/jpeg")
    }

    # Chọn URL theo MODE
    if MODE == "checkin":
        url = f"{API_BASE}/api/face/checkin"
        data = {"shift_id": str(SHIFT_ID)}
    else:
        url = f"{API_BASE}/api/face/checkout"
        data = {}

    try:
        res = requests.post(url, files=files, data=data, timeout=15)
        try:
            json_data = res.json()
        except Exception:
            print("[ERROR] Không parse được JSON từ server, status:", res.status_code)
            print("Text:", res.text[:500])
            return None

        return json_data
    except Exception as e:
        print("[ERROR] Gửi request tới API thất bại:", e)
        return None


# ================== VÒNG LẶP CHÍNH ==================

def main():
    print("=== AUTO ATTENDANCE RTSP ===")
    print("MODE:", MODE)
    print("RTSP_URL:", RTSP_URL)

    cap = cv2.VideoCapture(RTSP_URL)

    if not cap.isOpened():
        print("[ERROR] Không mở được RTSP stream. Kiểm tra lại RTSP_URL.")
        return

    last_capture_time = 0.0
    # Lưu thời điểm lần cuối cùng chấm công thành công cho mỗi employee_id
    last_success_time_by_emp = {}

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Không đọc được frame từ camera, thử lại...")
                time.sleep(1)
                continue

            # Hiển thị khung hình (optional, có thể tắt nếu không cần)
            cv2.imshow("RTSP Attendance", frame)

            now = time.time()

            # Mỗi CAPTURE_INTERVAL giây mới gửi 1 frame
            if now - last_capture_time >= CAPTURE_INTERVAL:
                last_capture_time = now
                print("\n[INFO] Chụp frame và gửi lên API...")
                result = send_frame_to_api(frame)

                if result is None:
                    print("[INFO] Không nhận được JSON hợp lệ từ server.")
                else:
                    # In kết quả ra để debug
                    print("[API RESPONSE]", result)

                    # Xử lý logic hiển thị đẹp hơn
                    if "error" in result:
                        print("[ERROR]", result["error"])
                    else:
                        matched = result.get("matched", False)

                        if matched:
                            emp_id = result.get("employee_id")
                            fullname = result.get("fullname", "Unknown")
                            msg = result.get("message", "")
                            distance = result.get("distance", None)

                            # Kiểm tra cooldown theo employee_id
                            last_t = last_success_time_by_emp.get(emp_id, 0)
                            if now - last_t < COOLDOWN_SECONDS:
                                print(
                                    f"[SKIP] {fullname} (ID {emp_id}) vừa được chấm công cách đây "
                                    f"{int(now - last_t)}s, bỏ qua để tránh trùng."
                                )
                            else:
                                # Cập nhật thời gian cuối cùng
                                last_success_time_by_emp[emp_id] = now
                                print("====== CHẤM CÔNG THÀNH CÔNG ======")
                                print("Nhân viên:", fullname, f"(ID: {emp_id})")
                                if distance is not None:
                                    print("Độ giống (distance):", distance)
                                print("Thông điệp:", msg)
                                print("===================================")
                        else:
                            # matched = False
                            print("[INFO] Không tìm được nhân viên khớp.")
                            msg = result.get("message")
                            if msg:
                                print("Chi tiết:", msg)

            # Bấm 'q' để thoát
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Thoát chương trình.")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

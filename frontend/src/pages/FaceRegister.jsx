// src/pages/FaceRegister.jsx
import React, { useEffect, useState } from "react";
import employeesApi from "../api/employeesApi";
import faceApi from "../api/faceApi";
import "./FaceRegister.css";

export default function FaceRegister() {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("");
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState("");

  // Lấy danh sách nhân viên cho combobox
  useEffect(() => {
    const loadEmployees = async () => {
      try {
        const res = await employeesApi.getAll();
        setEmployees(res.data || res);
      } catch (error) {
        console.error("Lỗi load danh sách nhân viên:", error);
      }
    };

    loadEmployees();
  }, []);

  // Khi chọn nhân viên
  const handleEmployeeChange = (e) => {
    setSelectedEmployeeId(e.target.value);
  };

  // Khi chọn file ảnh
  const handleFileChange = (e) => {
    const f = e.target.files[0];
    setFile(f || null);
    setMessage("");

    if (f) {
      const url = URL.createObjectURL(f);
      setPreviewUrl(url);
    } else {
      setPreviewUrl("");
    }
  };

  // Gửi ảnh lên backend để sinh face_embedding
  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");

    if (!selectedEmployeeId) {
      setMessage("Vui lòng chọn nhân viên trước.");
      return;
    }
    if (!file) {
      setMessage("Vui lòng chọn file ảnh khuôn mặt.");
      return;
    }

    try {
      setIsUploading(true);
      const res = await faceApi.uploadEmployeeFace(selectedEmployeeId, file);

      // Backend có thể trả { success: true, message: "...", embedding_dim: 512, ... }
      const data = res.data || res;
      if (data.error) {
        setMessage(`Lỗi: ${data.error}`);
      } else {
        setMessage(data.message || "Lưu khuôn mặt thành công!");
      }
    } catch (error) {
      console.error("Lỗi upload khuôn mặt:", error);
      setMessage("Lỗi server khi lưu khuôn mặt.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="face-register-page">
      <div className="face-register-left">
        <h1 className="face-register-title">Đăng ký khuôn mặt cho nhân viên</h1>
        <p className="face-register-subtitle">
          Chọn nhân viên sau đó tải lên một ảnh khuôn mặt rõ nét để hệ thống
          sinh đặc trưng (face embedding).
        </p>

        <form className="face-register-form" onSubmit={handleSubmit}>
          {/* CHỌN NHÂN VIÊN */}
          <label className="field-label">Nhân viên</label>
          <select
            className="select-employee"
            value={selectedEmployeeId}
            onChange={handleEmployeeChange}
          >
            <option value="">-- Chọn nhân viên --</option>
            {employees.map((emp) => (
              <option key={emp.employee_id} value={emp.employee_id}>
                {emp.fullname} ({emp.department})
              </option>
            ))}
          </select>

          {/* CHỌN ẢNH */}
          <label className="field-label">Ảnh khuôn mặt</label>
          <input type="file" accept="image/*" onChange={handleFileChange} />

          <p className="hint-text">
            Nên dùng ảnh nhìn thẳng, đủ sáng, không bị che mặt (kích thước 4x6
            càng tốt).
          </p>

          <button
            type="submit"
            className="btn-primary"
            disabled={isUploading}
          >
            {isUploading ? "Đang lưu..." : "Lưu khuôn mặt"}
          </button>

          {message && <p className="status-message">{message}</p>}
        </form>
      </div>

      {/* ẢNH XEM TRƯỚC */}
      <div className="face-register-preview">
        <h2 className="preview-title">Ảnh xem trước</h2>
        <div className="preview-box">
          {previewUrl ? (
            <img src={previewUrl} alt="Preview" className="preview-image" />
          ) : (
            <span className="preview-placeholder">Chưa chọn ảnh</span>
          )}
        </div>
      </div>
    </div>
  );
}

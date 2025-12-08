// src/pages/Employees.jsx
import React, { useEffect, useState } from "react";
import employeesApi from "../api/employeesApi";
import "./Employees.css";

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [form, setForm] = useState({
    fullname: "",
    email: "",
    phone: "",
    department: "",
    position: "",
  });

  // id nhân viên đang được sửa (null = thêm mới)
  const [editingId, setEditingId] = useState(null);

  useEffect(() => {
    loadEmployees();
  }, []);

  const loadEmployees = async () => {
    try {
      const res = await employeesApi.getAll();
      setEmployees(res.data || res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const resetForm = () => {
    setForm({
      fullname: "",
      email: "",
      phone: "",
      department: "",
      position: "",
    });
    setEditingId(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        // ĐANG SỬA
        await employeesApi.update(editingId, form);
      } else {
        // THÊM MỚI
        await employeesApi.create(form);
      }

      resetForm();
      loadEmployees();
    } catch (err) {
      console.error(err);
      alert("Lưu nhân viên thất bại, kiểm tra lại server!");
    }
  };

  const handleDelete = async (id) => {
    const ok = window.confirm("Bạn có chắc muốn xoá nhân viên này?");
    if (!ok) return;

    try {
      await employeesApi.remove(id);
      setEmployees((prev) => prev.filter((e) => e.employee_id !== id));
    } catch (error) {
      console.error("Lỗi xoá nhân viên:", error);
      alert("Xoá nhân viên thất bại, kiểm tra lại server!");
    }
  };

  // Khi bấm nút SỬA trên từng dòng
  const handleEdit = (emp) => {
    setEditingId(emp.employee_id); 
    setForm({
      fullname: emp.fullname || "",
      email: emp.email || "",
      phone: emp.phone || "",
      department: emp.department || "",
      position: emp.position || "",
    });
  };

  return (
    <div className="employees-page">
      <h1 className="employees-title">Quản lý nhân viên</h1>

      {/* CARD THÊM / SỬA NHÂN VIÊN */}
      <div className="card">
        <h2 className="card-title">
          {editingId ? "Cập nhật nhân viên" : "Thêm nhân viên mới"}
        </h2>

        <form className="employee-form" onSubmit={handleSubmit}>
          <div className="form-row">
            <input
              name="fullname"
              value={form.fullname}
              onChange={handleChange}
              placeholder="Họ và tên"
            />
            <input
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="Email"
            />
          </div>
          <div className="form-row">
            <input
              name="phone"
              value={form.phone}
              onChange={handleChange}
              placeholder="Số điện thoại"
            />
            <input
              name="department"
              value={form.department}
              onChange={handleChange}
              placeholder="Phòng ban"
            />
            <input
              name="position"
              value={form.position}
              onChange={handleChange}
              placeholder="Chức vụ"
            />
          </div>

          <div className="form-actions">
            <button type="submit">
              {editingId ? "Cập nhật" : "Lưu nhân viên"}
            </button>
            {editingId && (
              <button
                type="button"
                className="btn-cancel"
                onClick={resetForm}
              >
                Huỷ
              </button>
            )}
          </div>
        </form>
      </div>

      {/* BẢNG DANH SÁCH NHÂN VIÊN */}
      <div className="card table-card">
        <h2 className="card-title">Danh sách nhân viên</h2>
        <div className="table-wrapper">
          <table className="employees-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Họ tên</th>
                <th>Email</th>
                <th>Điện thoại</th>
                <th>Phòng ban</th>
                <th>Chức vụ</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((emp) => (
                <tr key={emp.employee_id}>
                  <td>{emp.employee_id}</td>
                  <td>{emp.fullname}</td>
                  <td>{emp.email}</td>
                  <td>{emp.phone}</td>
                  <td>{emp.department}</td>
                  <td>{emp.position}</td>
                  <td>
                    <button
                      className="btn-edit"
                      onClick={() => handleEdit(emp)}
                    >
                      Sửa
                    </button>
                    <button
                      className="btn-delete"
                      onClick={() => handleDelete(emp.employee_id)}
                    >
                      Xoá
                    </button>
                  </td>
                </tr>
              ))}
              {employees.length === 0 && (
                <tr>
                  <td colSpan="7" className="empty-text">
                    Chưa có nhân viên nào
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

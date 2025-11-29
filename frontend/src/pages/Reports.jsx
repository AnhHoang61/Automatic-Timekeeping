// src/pages/Reports.jsx
import React, { useEffect, useState } from "react";
import reportsApi from "../api/reportsApi";
import "./Reports.css";

export default function Reports() {
  const today = new Date().toISOString().slice(0, 10);
  const firstDay = today.slice(0, 8) + "01";

  const [filters, setFilters] = useState({
    from: firstDay,
    to: today,
    department: "Tất cả",
  });

  const [summary, setSummary] = useState(null);
  const [byDay, setByDay] = useState([]);
  const [byEmployee, setByEmployee] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFilters((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const loadReports = async () => {
    try {
      setLoading(true);
      const params = {
        from: filters.from,
        to: filters.to,
        department: filters.department === "Tất cả" ? "" : filters.department,
      };

      const [summaryRes, dayRes, empRes] = await Promise.all([
        reportsApi.summary(params),
        reportsApi.byDay(params),
        reportsApi.byEmployee(params),
      ]);

      setSummary(summaryRes.data);
      setByDay(dayRes.data);
      setByEmployee(empRes.data);
    } catch (err) {
      console.error("Lỗi tải báo cáo:", err);
      alert("Không tải được báo cáo, kiểm tra lại server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []); // lần đầu

  const handleExport = () => {
    const params = {
      from: filters.from,
      to: filters.to,
      department: filters.department === "Tất cả" ? "" : filters.department,
    };
    reportsApi.exportExcel(params);
  };

  return (
    <div className="reports-page">
      <h1 className="page-title">Báo cáo chấm công</h1>

      {/* FILTER BAR */}
      <div className="report-filters">
        <div className="filter-group">
          <label>Từ ngày</label>
          <input
            type="date"
            name="from"
            value={filters.from}
            onChange={handleChange}
          />
        </div>
        <div className="filter-group">
          <label>Đến ngày</label>
          <input
            type="date"
            name="to"
            value={filters.to}
            onChange={handleChange}
          />
        </div>
        <div className="filter-group">
          <label>Phòng ban</label>
          <select
            name="department"
            value={filters.department}
            onChange={handleChange}
          >
            <option>Tất cả</option>
            <option>Phòng IT</option>
            <option>Kinh doanh</option>
            <option>Nhân sự</option>
            {/* thêm các phòng ban khác nếu cần */}
          </select>
        </div>

        <button className="btn-primary" onClick={loadReports} disabled={loading}>
          {loading ? "Đang tải..." : "Lọc"}
        </button>

        <button className="btn-outline" onClick={handleExport}>
          Xuất Excel
        </button>
      </div>

      {/* SUMMARY CARDS */}
      {summary && (
        <div className="report-summary-grid">
          <div className="summary-card">
            <p>Số ngày làm việc</p>
            <h2>{summary.working_days}</h2>
          </div>
          <div className="summary-card">
            <p>Tổng công (giờ)</p>
            <h2>{summary.total_hours}</h2>
          </div>
          <div className="summary-card">
            <p>Số lượt đi trễ</p>
            <h2>{summary.late_count}</h2>
          </div>
          <div className="summary-card">
            <p>Số ngày vắng</p>
            <h2>{summary.absent_days}</h2>
          </div>
        </div>
      )}

      {/* BẢNG THEO NGÀY */}
      <div className="report-section daily-table">
        <h2>Tổng hợp theo ngày</h2>
        <table className="report-table">
          <thead>
            <tr>
              <th>Ngày</th>
              <th>Tổng NV</th>
              <th>Đã đi làm</th>
              <th>Đi trễ</th>
              <th>Vắng</th>
            </tr>
          </thead>
          <tbody>
            {byDay.map((row) => (
              <tr key={row.date}>
                <td>{row.date}</td>
                <td>{row.total_employees}</td>
                <td>{row.present}</td>
                <td>{row.late}</td>
                <td>{row.absent}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* BẢNG THEO NHÂN VIÊN */}
      <div className="report-section">
        <h2>Chi tiết theo nhân viên</h2>
        <table className="report-table">
          <thead>
            <tr>
              <th>Họ tên</th>
              <th>Phòng ban</th>
              <th>Ngày công</th>
              <th>Đi trễ</th>
              <th>Vắng</th>
            </tr>
          </thead>
          <tbody>
            {byEmployee.map((emp) => (
              <tr key={emp.employee_id}>
                <td>{emp.fullname}</td>
                <td>{emp.department}</td>
                <td>{emp.present_days}</td>
                <td>{emp.late_days}</td>
                <td>{emp.absent_days}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

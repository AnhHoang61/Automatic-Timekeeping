// src/pages/Dashboard.jsx
import React, { useEffect, useState } from "react";
import dashboardApi from "../api/dashboardApi";
import "./Dashboard.css";

export default function Dashboard() {
  const [date, setDate] = useState(() => {
    const d = new Date();
    return d.toISOString().slice(0, 10); // YYYY-MM-DD
  });

  const [summary, setSummary] = useState(null);
  const [todayLogs, setTodayLogs] = useState([]);
  const [topLate, setTopLate] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadDashboard = async (selectedDate = date) => {
    try {
      setLoading(true);
      const res = await dashboardApi.getDashboard(selectedDate);
      const data = res.data || res;
      setSummary(data.summary);
      setTodayLogs(data.today_logs);
      setTopLate(data.top_late);
    } catch (error) {
      console.error("Lỗi load dashboard:", error);
      alert("Không tải được dữ liệu dashboard, kiểm tra lại server!");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleDateChange = (e) => {
    const newDate = e.target.value;
    setDate(newDate);
    loadDashboard(newDate);
  };

  return (
    <div className="dashboard-page">
      {/* HEADER */}
      <div className="dashboard-header">
        <div>
          <h1>Dashboard chấm công HTCS</h1>
          <p className="dashboard-subtitle">
            Tổng quan tình hình chấm công theo ngày – dữ liệu thời gian thực
          </p>
        </div>

        <div className="dashboard-date">
          <label>Ngày</label>
          <input type="date" value={date} onChange={handleDateChange} />
        </div>
      </div>

      {loading && (
        <div className="loading-bar">
          <span>Đang tải dữ liệu...</span>
        </div>
      )}

      {/* KPI CARDS */}
      {summary && (
        <div className="kpi-grid">
          <div className="kpi-card kpi-primary">
            <p className="kpi-label">Tổng nhân viên</p>
            <h2 className="kpi-value">{summary.total_employees}</h2>
            <span className="kpi-desc">Đang hoạt động</span>
          </div>

          <div className="kpi-card">
            <p className="kpi-label">Đã check-in hôm nay</p>
            <h2 className="kpi-value">{summary.checked_in_today}</h2>
            <span className="kpi-desc">Tính đến {summary.date}</span>
          </div>

          <div className="kpi-card">
            <p className="kpi-label">Đang làm việc</p>
            <h2 className="kpi-value">{summary.working_now}</h2>
            <span className="kpi-desc">Đã check-in, chưa check-out</span>
          </div>

          <div className="kpi-card kpi-danger">
            <p className="kpi-label">Đi trễ</p>
            <h2 className="kpi-value">{summary.late_count}</h2>
            <span className="kpi-desc">So với giờ chuẩn ca sáng</span>
          </div>
        </div>
      )}

      {/* 2 CARD DƯỚI: CHẤM CÔNG HÔM NAY + TOP ĐI TRỄ */}
      <div className="dashboard-grid">
        {/* CHẤM CÔNG HÔM NAY */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2>Chấm công hôm nay</h2>
              <p className="card-subtitle">
              </p>
            </div>
          </div>

          <div className="table-wrapper">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Thời gian in</th>
                  <th>Nhân viên</th>
                  <th>Phòng ban</th>
                  <th>Ca</th>
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {todayLogs.map((row) => (
                  <tr key={row.log_id}>
                    <td>{row.check_in}</td>
                    <td>{row.fullname}</td>
                    <td>{row.department}</td>
                    <td>{row.shift_name}</td>
                    <td>
                      <span
                        className={
                          row.status === "LATE"
                            ? "badge badge-late"
                            : row.status === "PRESENT"
                            ? "badge badge-ok"
                            : "badge"
                        }
                      >
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}

                {todayLogs.length === 0 && (
                  <tr>
                    <td colSpan="5" className="empty-text">
                      Hôm nay chưa có chấm công nào
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* TOP ĐI TRỄ TRONG THÁNG */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2>Top đi trễ trong tháng</h2>
              <p className="card-subtitle">
              </p>
            </div>
          </div>

          <div className="table-wrapper">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Nhân viên</th>
                  <th>Phòng ban</th>
                  <th>Số lần trễ</th>
                </tr>
              </thead>
              <tbody>
                {topLate.map((row) => (
                  <tr key={row.employee_id}>
                    <td>{row.fullname}</td>
                    <td>{row.department}</td>
                    <td>{row.late_count}</td>
                  </tr>
                ))}

                {topLate.length === 0 && (
                  <tr>
                    <td colSpan="3" className="empty-text">
                      Chưa có ai đi trễ trong tháng này 🎉
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

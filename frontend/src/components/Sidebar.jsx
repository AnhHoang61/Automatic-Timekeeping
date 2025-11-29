import logo from "../assets/logo.png";
import { NavLink } from "react-router-dom";
import "./Sidebar.css";

export default function Sidebar() {
  return (
    <div className="sidebar">
      <img src={logo} className="logo" alt="HTCS Logo" />
      <h2>HTCS</h2>

      <div className="sidebar-menu">
        <NavLink to="/" end>Dashboard</NavLink>
        <NavLink to="/employees">Quản lý nhân viên</NavLink>
        <NavLink to="/face-register">Đăng ký khuôn mặt</NavLink>
        <NavLink to="/reports">Báo cáo</NavLink>
      </div>
    </div>
  );
}

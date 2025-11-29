import React from "react";
import Sidebar from "./Sidebar";
import "./Layout.css";

export default function Layout({ children }) {
  return (
    <div className="layout">
      <Sidebar />  
      <main className="content">
        <header className="header">
          <h1>Hệ thống chấm công tự động</h1>
        </header>
        <section className="page">{children}</section>
      </main>
    </div>
  );
}

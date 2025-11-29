// src/api/reportsApi.js
import axiosClient from "./axiosClient";

const reportsApi = {
  summary(params) {
    return axiosClient.get("/api/reports/summary", { params });
  },
  byDay(params) {
    return axiosClient.get("/api/reports/by-day", { params });
  },
  byEmployee(params) {
    return axiosClient.get("/api/reports/by-employee", { params });
  },
  exportExcel(params) {
    // dùng window.open cho đơn giản
    const searchParams = new URLSearchParams(params).toString();
    window.open(`${axiosClient.defaults.baseURL}/api/reports/export?${searchParams}`, "_blank");
  },
};

export default reportsApi;


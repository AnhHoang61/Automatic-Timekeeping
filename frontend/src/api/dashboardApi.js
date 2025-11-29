// src/api/dashboardApi.js
import axiosClient from "./axiosClient";

const dashboardApi = {
  // GET /api/dashboard?date=YYYY-MM-DD
  getDashboard(date) {
    return axiosClient.get("/api/dashboard", {
      params: { date },  // có thể null -> backend dùng hôm nay
    });
  },
};

export default dashboardApi;

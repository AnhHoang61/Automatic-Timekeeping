// src/api/axiosClient.js
import axios from "axios";

const axiosClient = axios.create({
  baseURL: "http://127.0.0.1:5000", // đổi nếu backend chạy port khác
  headers: {
    "Content-Type": "application/json",
  },
});

// interceptors: có thể log lỗi / thêm token về sau
axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API error:", error);
    throw error;
  }
);

export default axiosClient;

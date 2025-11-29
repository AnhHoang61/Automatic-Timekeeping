// src/api/faceApi.js
import axiosClient from "./axiosClient";

const faceApi = {
  /**
   * Upload ảnh khuôn mặt cho 1 nhân viên
   * @param {number} employeeId
   * @param {File} file - file ảnh
   */
  uploadEmployeeFace(employeeId, file) {
    const formData = new FormData();
    // TÊN 'image' phải trùng với backend (request.files["image"])
    formData.append("image", file);

    return axiosClient.post(`/api/employees/${employeeId}/face`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};

export default faceApi;

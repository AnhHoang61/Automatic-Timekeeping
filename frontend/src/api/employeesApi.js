// src/api/employeesApi.js
import axiosClient from "./axiosClient";

const employeesApi = {
  // GET /api/employees
  getAll() {
    return axiosClient.get("/api/employees");
  },

  // POST /api/employees
  create(data) {
    return axiosClient.post("/api/employees", data);
  },

  // PUT /api/employees/:id
  update(id, data) {
    return axiosClient.put(`/api/employees/${id}`, data);
  },

  // DELETE /api/employees/:id
  remove(id) {
    return axiosClient.delete(`/api/employees/${id}`);
  },
};

export default employeesApi;



import api from "./client";

export const usersApi = {
  updateProfile: (data) => api.patch("/api/users/me", data),
  changePassword: (data) => api.post("/api/users/me/change-password", data),
};

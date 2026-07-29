import api from "./client";

export const uploadsApi = {
  upload: (file, onProgress) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/api/uploads/", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total));
      },
    });
  },
  list: (page = 1, pageSize = 20) =>
    api.get("/api/uploads/", { params: { page, page_size: pageSize } }),
  delete: (id) => api.delete(`/api/uploads/${id}`),
};

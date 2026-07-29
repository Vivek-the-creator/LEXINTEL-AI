import { useState, useCallback, useRef, useEffect } from "react";
import {
  Upload, X, FileText, Image, Music, Video,
  Trash2, Eye, CheckCircle, AlertCircle, Loader2, FolderOpen
} from "lucide-react";
import { uploadsApi } from "../../api/uploads";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import { cn, formatBytes, formatRelativeTime, FILE_CATEGORY_ICONS } from "../../utils/helpers";
import toast from "react-hot-toast";

const ACCEPTED = ".pdf,.png,.jpg,.jpeg,.gif,.webp,.mp3,.wav,.mp4,.avi,.mov,.mkv";
const MAX_SIZE = 50 * 1024 * 1024;

function getFileIcon(mime) {
  if (mime?.startsWith("image/")) return Image;
  if (mime?.startsWith("audio/")) return Music;
  if (mime?.startsWith("video/")) return Video;
  return FileText;
}

function UploadItem({ item, onRemove }) {
  const Icon = getFileIcon(item.file?.type);
  const isImage = item.file?.type?.startsWith("image/");

  return (
    <div className={cn(
      "flex items-center gap-4 p-4 rounded-xl border transition-all",
      item.status === "error"
        ? "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/10"
        : item.status === "done"
        ? "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/10"
        : "border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-900"
    )}>
      <div className="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0 bg-surface-100 dark:bg-surface-800 flex items-center justify-center">
        {isImage && item.preview ? (
          <img src={item.preview} alt="" className="w-full h-full object-cover" />
        ) : (
          <Icon className="w-6 h-6 text-surface-400" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-surface-900 dark:text-surface-100 truncate">{item.file.name}</p>
        <p className="text-xs text-surface-400 dark:text-surface-500">{formatBytes(item.file.size)}</p>
        {item.status === "uploading" && (
          <div className="mt-2">
            <div className="flex justify-between text-xs text-surface-500 mb-1">
              <span>Uploading...</span>
              <span>{item.progress}%</span>
            </div>
            <div className="h-1.5 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-500 rounded-full transition-all duration-300"
                style={{ width: `${item.progress}%` }}
              />
            </div>
          </div>
        )}
        {item.status === "error" && (
          <p className="text-xs text-red-500 mt-1">{item.error}</p>
        )}
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {item.status === "uploading" && <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />}
        {item.status === "done" && <CheckCircle className="w-5 h-5 text-green-500" />}
        {item.status === "error" && <AlertCircle className="w-5 h-5 text-red-500" />}
        {item.status !== "uploading" && (
          <button
            onClick={() => onRemove(item.id)}
            className="p-1.5 rounded-lg text-surface-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

export default function UploadsPage() {
  const [queue, setQueue] = useState([]);
  const [uploads, setUploads] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const fetchUploads = useCallback(async () => {
    try {
      const res = await uploadsApi.list();
      setUploads(res.data.items || []);
    } catch {
      toast.error("Failed to load uploads");
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => { fetchUploads(); }, [fetchUploads]);

  const addFiles = useCallback((files) => {
    const newItems = Array.from(files)
      .filter((f) => {
        if (f.size > MAX_SIZE) { toast.error(`${f.name} exceeds 50MB limit`); return false; }
        return true;
      })
      .map((f) => ({
        id: `${Date.now()}-${Math.random()}`,
        file: f,
        status: "pending",
        progress: 0,
        preview: f.type.startsWith("image/") ? URL.createObjectURL(f) : null,
        error: null,
      }));
    setQueue((q) => [...q, ...newItems]);
  }, []);

  const uploadFile = useCallback(async (item) => {
    setQueue((q) => q.map((i) => i.id === item.id ? { ...i, status: "uploading" } : i));
    try {
      await uploadsApi.upload(item.file, (progress) => {
        setQueue((q) => q.map((i) => i.id === item.id ? { ...i, progress } : i));
      });
      setQueue((q) => q.map((i) => i.id === item.id ? { ...i, status: "done", progress: 100 } : i));
      toast.success(`${item.file.name} uploaded`);
      fetchUploads();
    } catch (err) {
      const msg = err?.response?.data?.detail || "Upload failed";
      setQueue((q) => q.map((i) => i.id === item.id ? { ...i, status: "error", error: msg } : i));
      toast.error(msg);
    }
  }, [fetchUploads]);

  const uploadAll = useCallback(() => {
    queue.filter((i) => i.status === "pending").forEach(uploadFile);
  }, [queue, uploadFile]);

  const removeFromQueue = useCallback((id) => {
    setQueue((q) => {
      const item = q.find((i) => i.id === id);
      if (item?.preview) URL.revokeObjectURL(item.preview);
      return q.filter((i) => i.id !== id);
    });
  }, []);

  const deleteUpload = useCallback(async (id) => {
    try {
      await uploadsApi.delete(id);
      setUploads((u) => u.filter((f) => f.id !== id));
      toast.success("File deleted");
    } catch {
      toast.error("Failed to delete file");
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  }, [addFiles]);

  const pendingCount = queue.filter((i) => i.status === "pending").length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100">File Uploads</h1>
        <p className="text-surface-500 dark:text-surface-400 mt-1">Upload and manage your legal documents, evidence, and media files.</p>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200",
          dragging
            ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20 scale-[1.01]"
            : "border-surface-300 dark:border-surface-600 hover:border-primary-400 dark:hover:border-primary-500 hover:bg-surface-50 dark:hover:bg-surface-800/50"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED}
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
        <div className={cn(
          "w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 transition-colors",
          dragging ? "bg-primary-100 dark:bg-primary-900/40" : "bg-surface-100 dark:bg-surface-800"
        )}>
          <Upload className={cn("w-8 h-8 transition-colors", dragging ? "text-primary-600" : "text-surface-400")} />
        </div>
        <p className="text-lg font-semibold text-surface-900 dark:text-surface-100 mb-1">
          {dragging ? "Drop files here" : "Drag & drop files here"}
        </p>
        <p className="text-sm text-surface-500 dark:text-surface-400 mb-4">or click to browse</p>
        <p className="text-xs text-surface-400 dark:text-surface-500">
          PDF, Images (PNG, JPG, GIF, WebP), Audio (MP3, WAV), Video (MP4, AVI, MOV) · Max 50MB per file
        </p>
      </div>

      {queue.length > 0 && (
        <div className="card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-surface-900 dark:text-surface-100">
              Upload Queue ({queue.length})
            </h2>
            <div className="flex gap-2">
              {pendingCount > 0 && (
                <Button size="sm" onClick={uploadAll}>
                  Upload All ({pendingCount})
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setQueue([])}
              >
                Clear
              </Button>
            </div>
          </div>
          <div className="space-y-3">
            {queue.map((item) => (
              <UploadItem key={item.id} item={item} onRemove={removeFromQueue} />
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="flex items-center justify-between p-6 border-b border-surface-200 dark:border-surface-700">
          <div className="flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-surface-500" />
            <h2 className="font-semibold text-surface-900 dark:text-surface-100">
              Uploaded Files {!loadingList && `(${uploads.length})`}
            </h2>
          </div>
        </div>

        {loadingList ? (
          <div className="p-6 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 p-4 rounded-xl border border-surface-200 dark:border-surface-700">
                <div className="w-12 h-12 rounded-lg bg-surface-200 dark:bg-surface-700 animate-pulse" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded animate-pulse w-1/2" />
                  <div className="h-3 bg-surface-200 dark:bg-surface-700 rounded animate-pulse w-1/4" />
                </div>
              </div>
            ))}
          </div>
        ) : uploads.length === 0 ? (
          <div className="p-16 text-center">
            <Upload className="w-12 h-12 text-surface-300 dark:text-surface-600 mx-auto mb-3" />
            <p className="text-surface-500 dark:text-surface-400">No files uploaded yet</p>
            <p className="text-sm text-surface-400 dark:text-surface-500 mt-1">Upload your first file above</p>
          </div>
        ) : (
          <div className="p-6 space-y-3">
            {uploads.map((file) => {
              const Icon = getFileIcon(file.mime_type);
              const isImage = file.mime_type?.startsWith("image/");
              return (
                <div key={file.id} className="flex items-center gap-4 p-4 rounded-xl border border-surface-200 dark:border-surface-700 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors group">
                  <div className="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0 bg-surface-100 dark:bg-surface-800 flex items-center justify-center">
                    {isImage ? (
                      <img
                        src={`${import.meta.env.VITE_API_BASE_URL}${file.url}`}
                        alt=""
                        className="w-full h-full object-cover"
                        onError={(e) => { e.target.style.display = "none"; }}
                      />
                    ) : (
                      <Icon className="w-6 h-6 text-surface-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-surface-900 dark:text-surface-100 truncate">
                      {file.original_filename}
                    </p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-surface-400">{formatBytes(file.file_size)}</span>
                      <span className="text-xs text-surface-300 dark:text-surface-600">·</span>
                      <span className="text-xs text-surface-400">{formatRelativeTime(file.created_at)}</span>
                      <span className="text-xs">{FILE_CATEGORY_ICONS[file.category]}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <a
                      href={`${import.meta.env.VITE_API_BASE_URL}${file.url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-lg text-surface-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
                      title="View file"
                    >
                      <Eye className="w-4 h-4" />
                    </a>
                    <button
                      onClick={() => deleteUpload(file.id)}
                      className="p-2 rounded-lg text-surface-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                      title="Delete file"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

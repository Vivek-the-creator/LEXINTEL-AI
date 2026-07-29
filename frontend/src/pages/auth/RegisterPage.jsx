import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Mail, Lock, Eye, EyeOff, User, Scale, Sun, Moon } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import { cn, getErrorMessage } from "../../utils/helpers";
import toast from "react-hot-toast";

const ROLES = [
  { value: "citizen", label: "Citizen", desc: "Seeking legal guidance", color: "border-blue-500 bg-blue-50 dark:bg-blue-900/20" },
  { value: "lawyer", label: "Lawyer", desc: "Legal professional", color: "border-purple-500 bg-purple-50 dark:bg-purple-900/20" },
  { value: "judge", label: "Judge", desc: "Judicial officer", color: "border-amber-500 bg-amber-50 dark:bg-amber-900/20" },
];

export default function RegisterPage() {
  const { register } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "citizen" });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const validate = () => {
    const errs = {};
    if (!form.full_name || form.full_name.length < 2) errs.full_name = "Full name must be at least 2 characters";
    if (!form.email) errs.email = "Email is required";
    if (!form.password || form.password.length < 8) errs.password = "Password must be at least 8 characters";
    else if (!/[A-Z]/.test(form.password)) errs.password = "Password must contain an uppercase letter";
    else if (!/[0-9]/.test(form.password)) errs.password = "Password must contain a digit";
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setLoading(true);
    try {
      await register(form);
      toast.success("Account created successfully!");
      navigate("/dashboard");
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const set = (field) => (e) => {
    setForm((f) => ({ ...f, [field]: e.target.value }));
    setErrors((er) => ({ ...er, [field]: "" }));
  };

  return (
    <div className="min-h-screen bg-surface-50 dark:bg-surface-950 flex flex-col">
      <div className="flex justify-between items-center p-6">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
            <Scale className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-surface-900 dark:text-surface-100">LexIntel AI</span>
        </Link>
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
        >
          {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>

      <div className="flex-1 flex items-center justify-center px-6 py-8">
        <div className="w-full max-w-lg animate-slide-up">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-surface-900 dark:text-surface-100">Create your account</h1>
            <p className="text-surface-500 dark:text-surface-400 mt-2">Join LexIntel AI and transform your legal practice</p>
          </div>

          <div className="card p-8 shadow-sm">
            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                label="Full Name"
                type="text"
                placeholder="John Doe"
                value={form.full_name}
                onChange={set("full_name")}
                error={errors.full_name}
                leftIcon={User}
                autoComplete="name"
              />
              <Input
                label="Email address"
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={set("email")}
                error={errors.email}
                leftIcon={Mail}
                autoComplete="email"
              />
              <Input
                label="Password"
                type={showPassword ? "text" : "password"}
                placeholder="Min 8 chars, 1 uppercase, 1 digit"
                value={form.password}
                onChange={set("password")}
                error={errors.password}
                leftIcon={Lock}
                rightElement={
                  <button type="button" onClick={() => setShowPassword((s) => !s)} className="text-surface-400 hover:text-surface-600 dark:hover:text-surface-300">
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                }
                autoComplete="new-password"
              />

              <div>
                <label className="label">I am a...</label>
                <div className="grid grid-cols-3 gap-3">
                  {ROLES.map(({ value, label, desc, color }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setForm((f) => ({ ...f, role: value }))}
                      className={cn(
                        "p-3 rounded-lg border-2 text-left transition-all duration-150",
                        form.role === value
                          ? color
                          : "border-surface-200 dark:border-surface-700 hover:border-surface-300 dark:hover:border-surface-600"
                      )}
                    >
                      <p className="text-sm font-semibold text-surface-900 dark:text-surface-100">{label}</p>
                      <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">{desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              <Button type="submit" loading={loading} className="w-full mt-2">
                Create Account
              </Button>
            </form>
          </div>

          <p className="text-center text-sm text-surface-500 dark:text-surface-400 mt-6">
            Already have an account?{" "}
            <Link to="/login" className="text-primary-600 dark:text-primary-400 font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

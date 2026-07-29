import { useState } from "react";
import { Link } from "react-router-dom";
import { Mail, Scale, ArrowLeft, Sun, Moon } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import toast from "react-hot-toast";

export default function ForgotPasswordPage() {
  const { theme, toggleTheme } = useTheme();
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) { toast.error("Please enter your email"); return; }
    setLoading(true);
    await new Promise((r) => setTimeout(r, 1000));
    setLoading(false);
    setSubmitted(true);
    toast.success("Reset instructions sent!");
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
        <button onClick={toggleTheme} className="p-2 rounded-lg text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors">
          {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>

      <div className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-md animate-slide-up">
          <Link to="/login" className="inline-flex items-center gap-2 text-sm text-surface-500 hover:text-surface-700 dark:hover:text-surface-300 mb-8 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to sign in
          </Link>

          {!submitted ? (
            <>
              <div className="mb-8">
                <h1 className="text-3xl font-bold text-surface-900 dark:text-surface-100">Reset password</h1>
                <p className="text-surface-500 dark:text-surface-400 mt-2">
                  Enter your email and we'll send you reset instructions.
                </p>
              </div>
              <form onSubmit={handleSubmit} className="space-y-5">
                <Input
                  label="Email address"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  leftIcon={Mail}
                />
                <Button type="submit" loading={loading} className="w-full">
                  Send Reset Instructions
                </Button>
              </form>
            </>
          ) : (
            <div className="card p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto mb-4">
                <Mail className="w-8 h-8 text-green-600 dark:text-green-400" />
              </div>
              <h2 className="text-xl font-bold text-surface-900 dark:text-surface-100 mb-2">Check your email</h2>
              <p className="text-surface-500 dark:text-surface-400 mb-6">
                We sent password reset instructions to <strong className="text-surface-700 dark:text-surface-300">{email}</strong>
              </p>
              <Link to="/login">
                <Button variant="secondary" className="w-full">Back to Sign In</Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

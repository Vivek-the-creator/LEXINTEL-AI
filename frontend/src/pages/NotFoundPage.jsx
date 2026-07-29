import { Link } from "react-router-dom";
import { Scale, ArrowLeft } from "lucide-react";
import Button from "../components/ui/Button";

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-surface-50 dark:bg-surface-950 flex flex-col items-center justify-center px-6">
      <div className="text-center animate-fade-in">
        <div className="w-20 h-20 rounded-2xl bg-primary-600 flex items-center justify-center mx-auto mb-8 shadow-lg shadow-primary-500/25">
          <Scale className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-8xl font-extrabold text-surface-200 dark:text-surface-800 mb-4">404</h1>
        <h2 className="text-2xl font-bold text-surface-900 dark:text-surface-100 mb-3">Page Not Found</h2>
        <p className="text-surface-500 dark:text-surface-400 max-w-md mx-auto mb-8">
          The page you're looking for doesn't exist or has been moved. Let's get you back on track.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link to="/dashboard">
            <Button>Go to Dashboard</Button>
          </Link>
          <Link to="/">
            <Button variant="secondary" className="gap-2">
              <ArrowLeft className="w-4 h-4" /> Back to Home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

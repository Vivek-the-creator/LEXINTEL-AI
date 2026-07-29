import { Link } from "react-router-dom";
import { Scale, Shield, Brain, FileSearch, ArrowRight, CheckCircle, Sun, Moon } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import Button from "../components/ui/Button";

const features = [
  { icon: Brain, title: "AI-Powered Analysis", desc: "Multi-agent AI system for deep legal document analysis and research." },
  { icon: FileSearch, title: "Smart Case Research", desc: "RAG-powered retrieval of similar judgments and legal precedents." },
  { icon: Shield, title: "Evidence Management", desc: "Organize, analyze, and present evidence with intelligent categorization." },
  { icon: Scale, title: "Outcome Prediction", desc: "Data-driven case outcome predictions based on historical judgments." },
];

const roles = [
  { role: "Citizen", desc: "Access legal guidance, understand your rights, and manage your cases.", color: "bg-blue-500" },
  { role: "Lawyer", desc: "Accelerate research, draft documents, and build stronger legal strategies.", color: "bg-purple-500" },
  { role: "Judge", desc: "Access comprehensive case analysis and relevant legal precedents.", color: "bg-amber-500" },
];

export default function LandingPage() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-surface-50 dark:bg-surface-950">
      <nav className="sticky top-0 z-50 bg-white/80 dark:bg-surface-900/80 backdrop-blur-md border-b border-surface-200 dark:border-surface-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
              <Scale className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-surface-900 dark:text-surface-100">LexIntel AI</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
            >
              {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <Link to="/login">
              <Button variant="ghost" size="sm">Sign In</Button>
            </Link>
            <Link to="/register">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      <section className="relative overflow-hidden py-24 lg:py-32">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-transparent to-purple-50 dark:from-primary-950/30 dark:to-purple-950/20" />
        <div className="absolute top-20 left-1/4 w-72 h-72 bg-primary-400/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-1/4 w-96 h-96 bg-purple-400/10 rounded-full blur-3xl" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 text-sm font-medium mb-8 animate-fade-in">
            <span className="w-2 h-2 rounded-full bg-primary-500 animate-pulse" />
            AI-Powered Legal Intelligence Platform
          </div>
          <h1 className="text-5xl lg:text-7xl font-extrabold text-surface-900 dark:text-surface-100 leading-tight mb-6 animate-slide-up">
            The Future of{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-purple-600">
              Legal Intelligence
            </span>
          </h1>
          <p className="text-xl text-surface-600 dark:text-surface-400 max-w-3xl mx-auto mb-10 animate-slide-up">
            LexIntel AI combines multi-agent artificial intelligence with legal expertise to transform how courts, lawyers, and citizens interact with the legal system.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up">
            <Link to="/register">
              <Button size="lg" className="gap-2 shadow-lg shadow-primary-500/25">
                Start for Free <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="secondary" size="lg">Sign In to Dashboard</Button>
            </Link>
          </div>
          <div className="flex flex-wrap justify-center gap-6 mt-12 text-sm text-surface-500 dark:text-surface-400">
            {["No credit card required", "Free to get started", "Enterprise-grade security"].map((item) => (
              <div key={item} className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-white dark:bg-surface-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-surface-900 dark:text-surface-100 mb-4">
              Powerful Features for Legal Professionals
            </h2>
            <p className="text-lg text-surface-600 dark:text-surface-400 max-w-2xl mx-auto">
              Everything you need to navigate the legal landscape with confidence and precision.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="card p-6 hover:shadow-md transition-shadow group">
                <div className="w-12 h-12 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mb-4 group-hover:bg-primary-600 transition-colors">
                  <Icon className="w-6 h-6 text-primary-600 dark:text-primary-400 group-hover:text-white transition-colors" />
                </div>
                <h3 className="font-semibold text-surface-900 dark:text-surface-100 mb-2">{title}</h3>
                <p className="text-sm text-surface-600 dark:text-surface-400">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-surface-900 dark:text-surface-100 mb-4">
              Built for Everyone in the Legal System
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {roles.map(({ role, desc, color }) => (
              <div key={role} className="card p-8 text-center hover:shadow-lg transition-shadow">
                <div className={`w-16 h-16 rounded-2xl ${color} flex items-center justify-center mx-auto mb-4 shadow-lg`}>
                  <Scale className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-surface-900 dark:text-surface-100 mb-3">{role}</h3>
                <p className="text-surface-600 dark:text-surface-400">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-gradient-to-r from-primary-600 to-primary-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
            Ready to Transform Your Legal Practice?
          </h2>
          <p className="text-primary-200 text-lg mb-8">
            Join thousands of legal professionals already using LexIntel AI.
          </p>
          <Link to="/register">
            <Button size="lg" className="bg-white text-primary-700 hover:bg-primary-50 shadow-xl">
              Get Started Today <ArrowRight className="w-5 h-5" />
            </Button>
          </Link>
        </div>
      </section>

      <footer className="bg-surface-900 dark:bg-surface-950 text-surface-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-primary-600 flex items-center justify-center">
              <Scale className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-semibold text-white">LexIntel AI</span>
          </div>
          <p className="text-sm">© {new Date().getFullYear()} LexIntel AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

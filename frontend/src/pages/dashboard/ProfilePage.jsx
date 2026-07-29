import { useState } from "react";
import { User, Mail, Shield, Lock, Eye, EyeOff, Save } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { usersApi } from "../../api/users";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Badge from "../../components/ui/Badge";
import { cn, ROLE_LABELS, ROLE_COLORS, getErrorMessage, formatDate } from "../../utils/helpers";
import toast from "react-hot-toast";

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [profileForm, setProfileForm] = useState({ full_name: user?.full_name || "" });
  const [profileLoading, setProfileLoading] = useState(false);

  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "" });
  const [pwErrors, setPwErrors] = useState({});
  const [pwLoading, setPwLoading] = useState(false);
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    if (!profileForm.full_name || profileForm.full_name.length < 2) {
      toast.error("Name must be at least 2 characters");
      return;
    }
    setProfileLoading(true);
    try {
      const res = await usersApi.updateProfile(profileForm);
      updateUser(res.data);
      toast.success("Profile updated");
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!pwForm.current_password) errs.current_password = "Required";
    if (!pwForm.new_password || pwForm.new_password.length < 8) errs.new_password = "Min 8 characters";
    else if (!/[A-Z]/.test(pwForm.new_password)) errs.new_password = "Must contain uppercase";
    else if (!/[0-9]/.test(pwForm.new_password)) errs.new_password = "Must contain a digit";
    if (Object.keys(errs).length) { setPwErrors(errs); return; }
    setPwLoading(true);
    try {
      await usersApi.changePassword(pwForm);
      toast.success("Password changed successfully");
      setPwForm({ current_password: "", new_password: "" });
      setPwErrors({});
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setPwLoading(false);
    }
  };

  const initials = user?.full_name?.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100">My Profile</h1>
        <p className="text-surface-500 dark:text-surface-400 mt-1">Manage your account information and security settings.</p>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-5 mb-6 pb-6 border-b border-surface-200 dark:border-surface-700">
          <div className="w-20 h-20 rounded-2xl bg-primary-600 flex items-center justify-center text-white text-2xl font-bold flex-shrink-0 shadow-lg shadow-primary-500/25">
            {initials}
          </div>
          <div>
            <h2 className="text-xl font-bold text-surface-900 dark:text-surface-100">{user?.full_name}</h2>
            <p className="text-surface-500 dark:text-surface-400 text-sm">{user?.email}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className={cn("badge", ROLE_COLORS[user?.role])}>{ROLE_LABELS[user?.role]}</span>
              <span className="text-xs text-surface-400">Member since {formatDate(user?.created_at)}</span>
            </div>
          </div>
        </div>

        <form onSubmit={handleProfileSave} className="space-y-4">
          <h3 className="font-semibold text-surface-900 dark:text-surface-100 flex items-center gap-2">
            <User className="w-4 h-4" /> Personal Information
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              value={profileForm.full_name}
              onChange={(e) => setProfileForm({ full_name: e.target.value })}
              leftIcon={User}
            />
            <Input
              label="Email Address"
              value={user?.email}
              leftIcon={Mail}
              disabled
              hint="Email cannot be changed"
            />
          </div>
          <div>
            <label className="label">Role</label>
            <div className="flex items-center gap-2 px-3.5 py-2.5 bg-surface-50 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg">
              <Shield className="w-4 h-4 text-surface-400" />
              <span className={cn("badge", ROLE_COLORS[user?.role])}>{ROLE_LABELS[user?.role]}</span>
              <span className="text-xs text-surface-400 ml-1">Role cannot be changed after registration</span>
            </div>
          </div>
          <div className="flex justify-end">
            <Button type="submit" loading={profileLoading} className="gap-2">
              <Save className="w-4 h-4" /> Save Changes
            </Button>
          </div>
        </form>
      </div>

      <div className="card p-6">
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <h3 className="font-semibold text-surface-900 dark:text-surface-100 flex items-center gap-2">
            <Lock className="w-4 h-4" /> Change Password
          </h3>
          <Input
            label="Current Password"
            type={showCurrent ? "text" : "password"}
            value={pwForm.current_password}
            onChange={(e) => { setPwForm((f) => ({ ...f, current_password: e.target.value })); setPwErrors((er) => ({ ...er, current_password: "" })); }}
            error={pwErrors.current_password}
            leftIcon={Lock}
            rightElement={
              <button type="button" onClick={() => setShowCurrent((s) => !s)} className="text-surface-400 hover:text-surface-600 dark:hover:text-surface-300">
                {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            }
          />
          <Input
            label="New Password"
            type={showNew ? "text" : "password"}
            placeholder="Min 8 chars, 1 uppercase, 1 digit"
            value={pwForm.new_password}
            onChange={(e) => { setPwForm((f) => ({ ...f, new_password: e.target.value })); setPwErrors((er) => ({ ...er, new_password: "" })); }}
            error={pwErrors.new_password}
            leftIcon={Lock}
            rightElement={
              <button type="button" onClick={() => setShowNew((s) => !s)} className="text-surface-400 hover:text-surface-600 dark:hover:text-surface-300">
                {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            }
          />
          <div className="flex justify-end">
            <Button type="submit" loading={pwLoading} variant="secondary" className="gap-2">
              <Lock className="w-4 h-4" /> Update Password
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

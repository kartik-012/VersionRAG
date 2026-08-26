import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Layers, ArrowRight, ArrowLeft, Lock, Mail, User as UserIcon,
  ShieldAlert, Eye, EyeOff, Check, CheckCircle2, RefreshCw,
  Sparkles, KeyRound, Zap, Shield
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../lib/api';
import { User } from '../types';

interface AuthViewProps {
  onAuthenticated: (user: User) => void;
}

type AuthStep = 'auth' | 'verify' | 'success' | 'forgot';

export const AuthView: React.FC<AuthViewProps> = ({ onAuthenticated }) => {
  const [step, setStep] = useState<AuthStep>('auth');
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // OTP state
  const [otpDigits, setOtpDigits] = useState<string[]>(['', '', '', '', '', '']);
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);
  const [resendCooldown, setResendCooldown] = useState(0);

  // Password strength
  const passwordStrength = useCallback((pw: string) => {
    let score = 0;
    if (pw.length >= 10) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    if (pw.length >= 14) score++;
    return score;
  }, []);

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = setInterval(() => setResendCooldown((c) => c - 1), 1000);
    return () => clearInterval(t);
  }, [resendCooldown]);

  // OTP input handlers
  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const newDigits = [...otpDigits];
    newDigits[index] = value.slice(-1);
    setOtpDigits(newDigits);
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newDigits = [...otpDigits];
    for (let i = 0; i < 6; i++) {
      newDigits[i] = pasted[i] || '';
    }
    setOtpDigits(newDigits);
    const focusIdx = Math.min(pasted.length, 5);
    otpRefs.current[focusIdx]?.focus();
  };

  // Auth form submit (Login or Signup)
  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isLogin) {
        const res = await api.login(email, password);
        onAuthenticated(res.user);
      } else {
        const res = await api.signup(email, fullName, password);
        if (res.requires_verification) {
          setStep('verify');
          setResendCooldown(60);
        }
      }
    } catch (err: any) {
      const msg = err.message || 'Authentication failed';
      if (msg === 'EMAIL_NOT_VERIFIED') {
        setStep('verify');
        setResendCooldown(0);
        setError(null);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  // OTP verification submit
  const handleVerifySubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const code = otpDigits.join('');
    if (code.length !== 6) {
      setError('Please enter all 6 digits of the verification code.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await api.verifyEmail(email, code);
      setStep('success');
      setSuccessMessage('Email successfully verified!');

      // Auto-login after verification
      setTimeout(async () => {
        try {
          const loginRes = await api.login(email, password);
          onAuthenticated(loginRes.user);
        } catch {
          setStep('auth');
          setIsLogin(true);
          setSuccessMessage('Email verified! Please sign in with your credentials.');
        }
      }, 2500);
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Auto-submit when all 6 digits are filled
  useEffect(() => {
    if (step === 'verify' && otpDigits.every((d) => d !== '')) {
      handleVerifySubmit();
    }
  }, [otpDigits, step]);

  // Resend OTP
  const handleResend = async () => {
    if (resendCooldown > 0) return;
    setLoading(true);
    setError(null);
    try {
      await api.resendVerification(email);
      setResendCooldown(60);
      setOtpDigits(['', '', '', '', '', '']);
      otpRefs.current[0]?.focus();
      setSuccessMessage('A new verification code has been sent to your email.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to resend code.');
    } finally {
      setLoading(false);
    }
  };

  // Forgot password
  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.forgotPassword(email);
      setSuccessMessage('If that email is registered, a password reset link has been sent.');
      setTimeout(() => {
        setStep('auth');
        setIsLogin(true);
        setSuccessMessage(null);
      }, 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to send reset email.');
    } finally {
      setLoading(false);
    }
  };

  const strength = passwordStrength(password);
  const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong', 'Excellent'];
  const strengthColors = ['', '#ef4444', '#f59e0b', '#eab308', '#22c55e', '#10b981'];

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background relative overflow-hidden">
      {/* Animated Background Gradient Orbs */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.08, 0.15, 0.08],
        }}
        transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute -top-40 -left-40 w-[500px] h-[500px] bg-blue-500 rounded-full blur-[120px] pointer-events-none"
      />
      <motion.div
        animate={{
          scale: [1.2, 1, 1.2],
          opacity: [0.06, 0.12, 0.06],
        }}
        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute -bottom-40 -right-40 w-[500px] h-[500px] bg-indigo-600 rounded-full blur-[120px] pointer-events-none"
      />
      <motion.div
        animate={{
          scale: [1, 1.15, 1],
          opacity: [0.04, 0.08, 0.04],
        }}
        transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute top-1/3 right-1/4 w-[350px] h-[350px] bg-emerald-500 rounded-full blur-[100px] pointer-events-none"
      />

      {/* Floating Particle Dots */}
      {[...Array(12)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-white/20"
          style={{
            left: `${10 + (i * 7.5) % 80}%`,
            top: `${15 + (i * 11.3) % 70}%`,
          }}
          animate={{
            y: [0, -20, 0],
            opacity: [0.15, 0.4, 0.15],
          }}
          transition={{
            duration: 3 + (i % 3),
            repeat: Infinity,
            delay: i * 0.3,
            ease: 'easeInOut',
          }}
        />
      ))}

      {/* Main Auth Container */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md relative z-10"
      >
        <AnimatePresence mode="wait">
          {/* ============ STEP 1: Sign Up / Sign In ============ */}
          {step === 'auth' && (
            <motion.div
              key="auth"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="glass-panel rounded-3xl shadow-2xl p-8 space-y-6 border border-surface-border glow-primary"
            >
              {/* Brand Header */}
              <div className="text-center">
                <motion.div
                  whileHover={{ rotate: 12, scale: 1.1 }}
                  className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary via-indigo-600 to-cyan-500 shadow-lg shadow-primary/40 mb-4 text-white"
                >
                  <Layers className="w-7 h-7" />
                </motion.div>
                <h1 className="text-2xl font-bold text-white tracking-tight">VersionRAG</h1>
                <p className="text-xs text-gray-400 mt-1">
                  Version-Aware Documentation Intelligence Platform
                </p>
              </div>

              {/* Tab Switcher */}
              <div className="flex bg-surface-subtle/80 rounded-2xl p-1 border border-surface-border">
                <button
                  onClick={() => { setIsLogin(true); setError(null); }}
                  className={`flex-1 py-2.5 rounded-xl text-xs font-semibold transition ${
                    isLogin
                      ? 'bg-primary text-white shadow-md shadow-primary/30'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Sign In
                </button>
                <button
                  onClick={() => { setIsLogin(false); setError(null); }}
                  className={`flex-1 py-2.5 rounded-xl text-xs font-semibold transition ${
                    !isLogin
                      ? 'bg-primary text-white shadow-md shadow-primary/30'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Create Account
                </button>
              </div>

              {/* Auth Form */}
              <form onSubmit={handleAuthSubmit} className="space-y-4">
                {!isLogin && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <label className="block text-xs font-medium text-gray-300 mb-1.5">Full Name</label>
                    <div className="relative">
                      <UserIcon className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
                      <input
                        type="text"
                        required
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="e.g. Alex Mercer"
                        className="w-full bg-background/80 border border-surface-border rounded-xl pl-10 pr-3 py-2.5 text-sm text-white focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition"
                      />
                    </div>
                  </motion.div>
                )}

                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1.5">Email Address</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@company.com"
                      className="w-full bg-background/80 border border-surface-border rounded-xl pl-10 pr-3 py-2.5 text-sm text-white focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-medium text-gray-300">Password</label>
                    {isLogin && (
                      <button
                        type="button"
                        onClick={() => { setStep('forgot'); setError(null); }}
                        className="text-[11px] text-primary-light hover:underline"
                      >
                        Forgot password?
                      </button>
                    )}
                  </div>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Min 10 characters, 1 uppercase, 1 digit"
                      className="w-full bg-background/80 border border-surface-border rounded-xl pl-10 pr-10 py-2.5 text-sm text-white focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-2.5 text-gray-400 hover:text-white transition"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>

                  {/* Password Strength Meter (Sign Up only) */}
                  {!isLogin && password.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="mt-2 space-y-1"
                    >
                      <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map((level) => (
                          <div
                            key={level}
                            className="h-1.5 flex-1 rounded-full transition-colors"
                            style={{
                              backgroundColor: strength >= level ? strengthColors[strength] : 'rgba(255,255,255,0.08)',
                            }}
                          />
                        ))}
                      </div>
                      <p className="text-[11px] font-medium" style={{ color: strengthColors[strength] || '#6b7280' }}>
                        {strengthLabels[strength] || 'Type a password'}
                      </p>
                    </motion.div>
                  )}
                </div>

                {/* Error Banner */}
                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -5 }}
                      className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2 glow-rose"
                    >
                      <ShieldAlert className="w-4 h-4 shrink-0" />
                      <span>{error}</span>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Success Banner */}
                <AnimatePresence>
                  {successMessage && (
                    <motion.div
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -5 }}
                      className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 glow-emerald"
                    >
                      <CheckCircle2 className="w-4 h-4 shrink-0" />
                      <span>{successMessage}</span>
                    </motion.div>
                  )}
                </AnimatePresence>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-primary hover:bg-primary-hover text-white text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shadow-primary/30 transition disabled:opacity-50 glow-primary"
                >
                  {loading ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <span>{isLogin ? 'Sign In to Workspace' : 'Create Account & Verify'}</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </motion.button>
              </form>

              {/* Security Footer */}
              <div className="pt-2 text-center">
                <p className="text-[11px] text-gray-500 flex items-center justify-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-gray-600" />
                  {isLogin
                    ? 'Your session is protected with JWT & bcrypt.'
                    : 'A verification code will be sent to your email.'}
                </p>
              </div>
            </motion.div>
          )}

          {/* ============ STEP 2: OTP Email Verification ============ */}
          {step === 'verify' && (
            <motion.div
              key="verify"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="glass-panel rounded-3xl shadow-2xl p-8 space-y-6 border border-surface-border glow-primary"
            >
              <div className="text-center">
                <motion.div
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity, repeatDelay: 3 }}
                  className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 shadow-lg shadow-emerald-500/30 mb-4 text-white"
                >
                  <Mail className="w-7 h-7" />
                </motion.div>
                <h2 className="text-xl font-bold text-white tracking-tight">Check Your Email</h2>
                <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                  We sent a 6-digit verification code to<br />
                  <span className="text-blue-400 font-semibold">{email}</span>
                </p>
              </div>

              {/* 6-Digit OTP Input */}
              <form onSubmit={handleVerifySubmit} className="space-y-5">
                <div className="flex justify-center gap-3" onPaste={handleOtpPaste}>
                  {otpDigits.map((digit, i) => (
                    <motion.input
                      key={i}
                      ref={(el) => { otpRefs.current[i] = el; }}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpChange(i, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(i, e)}
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: i * 0.06 }}
                      className={`w-12 h-14 text-center text-2xl font-bold font-mono rounded-xl border-2 bg-background/80 text-white focus:outline-none transition ${
                        digit
                          ? 'border-primary shadow-md shadow-primary/20 glow-primary'
                          : 'border-surface-border focus:border-primary'
                      }`}
                    />
                  ))}
                </div>

                {/* Error / Success */}
                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2"
                    >
                      <ShieldAlert className="w-4 h-4 shrink-0" />
                      <span>{error}</span>
                    </motion.div>
                  )}
                  {successMessage && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2"
                    >
                      <CheckCircle2 className="w-4 h-4 shrink-0" />
                      <span>{successMessage}</span>
                    </motion.div>
                  )}
                </AnimatePresence>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  type="submit"
                  disabled={loading || otpDigits.some((d) => !d)}
                  className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/30 transition disabled:opacity-50 glow-emerald"
                >
                  {loading ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <span>Verify Email Address</span>
                      <Check className="w-4 h-4" />
                    </>
                  )}
                </motion.button>
              </form>

              {/* Resend & Back */}
              <div className="flex items-center justify-between text-xs">
                <button
                  onClick={() => {
                    setStep('auth');
                    setError(null);
                    setOtpDigits(['', '', '', '', '', '']);
                  }}
                  className="text-gray-400 hover:text-white flex items-center gap-1 transition"
                >
                  <ArrowLeft className="w-3.5 h-3.5" /> Back to Sign In
                </button>

                <button
                  onClick={handleResend}
                  disabled={resendCooldown > 0 || loading}
                  className="text-primary-light hover:text-white font-medium disabled:text-gray-500 transition"
                >
                  {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend Code'}
                </button>
              </div>

              <p className="text-center text-[11px] text-gray-500">
                Code expires in {15} minutes. Check your spam folder if you don't see the email.
              </p>
            </motion.div>
          )}

          {/* ============ STEP 3: Success Animation ============ */}
          {step === 'success' && (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ type: 'spring' as const, stiffness: 200, damping: 20 }}
              className="glass-panel rounded-3xl shadow-2xl p-10 border border-emerald-500/40 text-center space-y-6 glow-emerald"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring' as const, stiffness: 250, damping: 15, delay: 0.15 }}
                className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-emerald-500 to-cyan-500 shadow-xl shadow-emerald-500/40 text-white"
              >
                <CheckCircle2 className="w-10 h-10" />
              </motion.div>

              <motion.h2
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-xl font-bold text-white"
              >
                Email Verified Successfully!
              </motion.h2>

              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="text-xs text-gray-400 leading-relaxed"
              >
                Your account is now fully active. Redirecting you to the VersionRAG platform...
              </motion.p>

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 }}
                className="flex items-center justify-center gap-2 text-xs text-emerald-300"
              >
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Signing you in automatically...</span>
              </motion.div>
            </motion.div>
          )}

          {/* ============ FORGOT PASSWORD ============ */}
          {step === 'forgot' && (
            <motion.div
              key="forgot"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="glass-panel rounded-3xl shadow-2xl p-8 space-y-6 border border-surface-border glow-primary"
            >
              <div className="text-center">
                <motion.div
                  whileHover={{ scale: 1.1 }}
                  className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 shadow-lg shadow-amber-500/30 mb-4 text-white"
                >
                  <KeyRound className="w-7 h-7" />
                </motion.div>
                <h2 className="text-xl font-bold text-white tracking-tight">Reset Your Password</h2>
                <p className="text-xs text-gray-400 mt-2">
                  Enter your email address and we'll send you a password reset link.
                </p>
              </div>

              <form onSubmit={handleForgotPassword} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1.5">Email Address</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@company.com"
                      className="w-full bg-background/80 border border-surface-border rounded-xl pl-10 pr-3 py-2.5 text-sm text-white focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition"
                    />
                  </div>
                </div>

                <AnimatePresence>
                  {error && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 shrink-0" />
                      <span>{error}</span>
                    </motion.div>
                  )}
                  {successMessage && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 shrink-0" />
                      <span>{successMessage}</span>
                    </motion.div>
                  )}
                </AnimatePresence>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shadow-amber-600/30 transition disabled:opacity-50 glow-amber"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <span>Send Reset Link</span>}
                </motion.button>
              </form>

              <button
                onClick={() => { setStep('auth'); setError(null); setSuccessMessage(null); }}
                className="w-full text-center text-xs text-gray-400 hover:text-white flex items-center justify-center gap-1 transition"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back to Sign In
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

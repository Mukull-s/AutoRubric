'use client';

import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ShieldCheck, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { z } from 'zod';

const registerSchema = z.object({
  full_name: z.string().optional(),
  email: z.string().email("Invalid email address"),
  password: z.string()
    .min(10, "Password must be at least 10 characters")
    .max(128, "Password must be at most 128 characters"),
  confirm_password: z.string(),
  registration_code: z.string().optional()
}).refine((data) => data.password === data.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
}).refine((data) => data.password.toLowerCase() !== data.email.toLowerCase(), {
  message: "Password cannot be the same as email",
  path: ["password"],
});

type RegisterFormData = z.infer<typeof registerSchema>;
type RegisterField = 'full_name' | 'email' | 'password' | 'confirm_password' | 'registration_code';
type FormErrors = Partial<Record<RegisterField, string>>;

export default function RegisterPage() {
  const { doRegister, token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (token) {
      router.push('/');
    }
  }, [token, router]);

  const [formData, setFormData] = useState<RegisterFormData>({
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
    registration_code: ''
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [serverError, setServerError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const fullNameRef = useRef<HTMLInputElement>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const confirmPasswordRef = useRef<HTMLInputElement>(null);
  const registrationCodeRef = useRef<HTMLInputElement>(null);

  const getFieldRef = (field: RegisterField) => {
    switch (field) {
      case 'full_name': return fullNameRef;
      case 'email': return emailRef;
      case 'password': return passwordRef;
      case 'confirm_password': return confirmPasswordRef;
      case 'registration_code': return registrationCodeRef;
    }
  };

  const getPasswordStrength = (pass: string) => {
    if (!pass) return '';
    if (pass.length < 10) return 'Weak';
    if (pass.length >= 10 && /[A-Z]/.test(pass) && /[0-9]/.test(pass)) return 'Strong';
    return 'Fair';
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    if (errors[e.target.name as RegisterField]) {
      setErrors(prev => ({ ...prev, [e.target.name]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;
    
    setServerError('');
    setErrors({});
    
    const result = registerSchema.safeParse(formData);
    
    if (!result.success) {
      const fieldErrors: FormErrors = {};
      let firstErrorField: RegisterField | null = null;
      
      result.error.issues.forEach(issue => {
        const path = issue.path[0] as RegisterField;
        if (!fieldErrors[path]) {
          fieldErrors[path] = issue.message;
          if (!firstErrorField) firstErrorField = path;
        }
      });
      
      setErrors(fieldErrors);
      
      if (firstErrorField) {
        const targetRef = getFieldRef(firstErrorField);
        targetRef?.current?.focus();
      }
      return;
    }

    setIsLoading(true);
    try {
      await doRegister({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name || undefined,
        registration_code: formData.registration_code || undefined
      });
    } catch (err: any) {
      try {
        const errBody = JSON.parse(err.message);
        setServerError(errBody.detail || 'Registration failed');
      } catch {
        setServerError(err instanceof Error ? err.message : 'Registration failed');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 overflow-hidden">
      <div className="ambient-glow -top-32 -left-32 w-96 h-96 bg-blue-100/60" />
      <div className="ambient-glow -bottom-32 -right-32 w-96 h-96 bg-purple-100/50" />
      <div className="ambient-glow top-1/3 right-1/4 w-80 h-80 bg-zinc-200/40" />

      <div className="relative w-full max-w-[420px] glass-card rounded-3xl p-8 sm:p-10 transition-all duration-300">
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-zinc-900 flex items-center justify-center text-white shadow-md mb-4">
            <ShieldCheck className="w-6 h-6 stroke-[1.75]" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            Create an Account
          </h1>
        </div>

        {serverError && (
          <div role="alert" className="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 text-xs text-center font-medium">
            {serverError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <label className="block">
            <span className="block text-xs font-medium text-zinc-600 mb-1.5 ml-1">
              Full Name <span className="text-zinc-400 font-normal">(Optional)</span>
            </span>
            <input
              ref={fullNameRef}
              type="text"
              name="full_name"
              autoComplete="name"
              className="w-full px-4 py-2.5 rounded-xl bg-white/70 border border-black/[0.08] text-sm text-zinc-900 placeholder:text-zinc-400 focus:bg-white focus:border-zinc-900 focus:ring-4 focus:ring-zinc-900/5 outline-none transition-all duration-200"
              placeholder="Jane Doe"
              value={formData.full_name}
              onChange={handleChange}
              aria-invalid={!!errors.full_name}
              aria-describedby={errors.full_name ? "full_name-error" : undefined}
            />
            {errors.full_name && <p id="full_name-error" className="text-red-500 text-xs mt-1 ml-1">{errors.full_name}</p>}
          </label>

          <label className="block">
            <span className="block text-xs font-medium text-zinc-600 mb-1.5 ml-1">Email *</span>
            <input
              ref={emailRef}
              type="email"
              name="email"
              autoComplete="email"
              className="w-full px-4 py-2.5 rounded-xl bg-white/70 border border-black/[0.08] text-sm text-zinc-900 placeholder:text-zinc-400 focus:bg-white focus:border-zinc-900 focus:ring-4 focus:ring-zinc-900/5 outline-none transition-all duration-200"
              placeholder="name@example.com"
              value={formData.email}
              onChange={handleChange}
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? "email-error" : undefined}
            />
            {errors.email && <p id="email-error" className="text-red-500 text-xs mt-1 ml-1">{errors.email}</p>}
          </label>

          <div className="block relative">
            <label>
              <span className="block text-xs font-medium text-zinc-600 mb-1.5 ml-1 flex justify-between">
                <span>Password *</span>
                {formData.password && (
                  <span className={`text-[10px] ${getPasswordStrength(formData.password) === 'Strong' ? 'text-green-600' : 'text-orange-500'}`}>
                    {getPasswordStrength(formData.password)}
                  </span>
                )}
              </span>
              <div className="relative">
                <input
                  ref={passwordRef}
                  type={showPassword ? "text" : "password"}
                  name="password"
                  autoComplete="new-password"
                  className="w-full px-4 py-2.5 pr-10 rounded-xl bg-white/70 border border-black/[0.08] text-sm text-zinc-900 placeholder:text-zinc-400 focus:bg-white focus:border-zinc-900 focus:ring-4 focus:ring-zinc-900/5 outline-none transition-all duration-200"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? "password-error" : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 focus:outline-none"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </label>
            {errors.password && <p id="password-error" className="text-red-500 text-xs mt-1 ml-1">{errors.password}</p>}
          </div>

          <label className="block">
            <span className="block text-xs font-medium text-zinc-600 mb-1.5 ml-1">Confirm Password *</span>
            <input
              ref={confirmPasswordRef}
              type={showPassword ? "text" : "password"}
              name="confirm_password"
              autoComplete="new-password"
              className="w-full px-4 py-2.5 rounded-xl bg-white/70 border border-black/[0.08] text-sm text-zinc-900 placeholder:text-zinc-400 focus:bg-white focus:border-zinc-900 focus:ring-4 focus:ring-zinc-900/5 outline-none transition-all duration-200"
              placeholder="••••••••"
              value={formData.confirm_password}
              onChange={handleChange}
              aria-invalid={!!errors.confirm_password}
              aria-describedby={errors.confirm_password ? "confirm_password-error" : undefined}
            />
            {errors.confirm_password && <p id="confirm_password-error" className="text-red-500 text-xs mt-1 ml-1">{errors.confirm_password}</p>}
          </label>

          <label className="block">
            <span className="block text-xs font-medium text-zinc-600 mb-1.5 ml-1">
              Invite Code <span className="text-zinc-400 font-normal">(Optional)</span>
            </span>
            <input
              ref={registrationCodeRef}
              type="text"
              name="registration_code"
              className="w-full px-4 py-2.5 rounded-xl bg-white/70 border border-black/[0.08] text-sm text-zinc-900 placeholder:text-zinc-400 focus:bg-white focus:border-zinc-900 focus:ring-4 focus:ring-zinc-900/5 outline-none transition-all duration-200"
              placeholder="XXXX-XXXX"
              value={formData.registration_code}
              onChange={handleChange}
              aria-invalid={!!errors.registration_code}
              aria-describedby={errors.registration_code ? "registration_code-error" : undefined}
            />
            {errors.registration_code && <p id="registration_code-error" className="text-red-500 text-xs mt-1 ml-1">{errors.registration_code}</p>}
          </label>

          <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-zinc-900 hover:bg-black text-white text-sm font-medium tracking-tight shadow-sm hover:shadow transition-all duration-200 disabled:opacity-50 active:scale-[0.99]"
            >
              <span>{isLoading ? 'Creating account...' : 'Sign Up'}</span>
              {!isLoading && <ArrowRight className="w-4 h-4 stroke-[2]" />}
            </button>
          </div>
        </form>

        <div className="mt-8 pt-6 border-t border-black/[0.04] text-center flex flex-col items-center gap-3">
          <Link href="/login" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors">
            Already have an account? Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}

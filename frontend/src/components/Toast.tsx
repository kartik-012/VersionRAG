import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  title: string;
  description?: string;
}

interface ToastContainerProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
      <AnimatePresence>
        {toasts.map((t) => {
          const config = {
            success: {
              icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
              border: 'border-emerald-500/30',
              bg: 'bg-surface/95',
            },
            error: {
              icon: <AlertCircle className="w-4 h-4 text-rose-400" />,
              border: 'border-rose-500/30',
              bg: 'bg-surface/95',
            },
            info: {
              icon: <Info className="w-4 h-4 text-blue-400" />,
              border: 'border-blue-500/30',
              bg: 'bg-surface/95',
            },
          }[t.type];

          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.15 } }}
              transition={{ type: 'spring', stiffness: 450, damping: 30 }}
              className={`pointer-events-auto p-4 rounded-xl border ${config.border} ${config.bg} backdrop-blur-xl shadow-2xl flex items-start gap-3`}
            >
              <div className="shrink-0 mt-0.5">{config.icon}</div>
              <div className="flex-1 text-xs">
                <h5 className="font-semibold text-white">{t.title}</h5>
                {t.description && <p className="text-gray-400 mt-0.5">{t.description}</p>}
              </div>
              <button
                onClick={() => onDismiss(t.id)}
                className="shrink-0 text-gray-500 hover:text-white p-0.5"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
};

export function formatPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export function getSeverityStyle(classId: number): {
  bg: string;
  text: string;
  border: string;
  badge: string;
  glow: string;
  color: string;
} {
  switch (classId) {
    case 0:
      return {
        bg: 'bg-emerald-950/40',
        text: 'text-emerald-400',
        border: 'border-emerald-500/40',
        badge: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
        glow: 'shadow-glow-emerald',
        color: '#10b981'
      };
    case 1:
      return {
        bg: 'bg-blue-950/40',
        text: 'text-blue-400',
        border: 'border-blue-500/40',
        badge: 'bg-blue-500/20 text-blue-300 border border-blue-500/30',
        glow: 'shadow-glow-blue',
        color: '#38a9f8'
      };
    case 2:
      return {
        bg: 'bg-amber-950/40',
        text: 'text-amber-400',
        border: 'border-amber-500/40',
        badge: 'bg-amber-500/20 text-amber-300 border border-amber-500/30',
        glow: 'shadow-[0_0_25px_-5px_rgba(245,158,11,0.25)]',
        color: '#f59e0b'
      };
    case 3:
      return {
        bg: 'bg-orange-950/40',
        text: 'text-orange-400',
        border: 'border-orange-500/40',
        badge: 'bg-orange-500/20 text-orange-300 border border-orange-500/30',
        glow: 'shadow-[0_0_25px_-5px_rgba(249,115,22,0.25)]',
        color: '#f97316'
      };
    case 4:
      return {
        bg: 'bg-rose-950/40',
        text: 'text-rose-400',
        border: 'border-rose-500/40',
        badge: 'bg-rose-500/20 text-rose-300 border border-rose-500/30',
        glow: 'shadow-glow-red',
        color: '#f43f5e'
      };
    default:
      return {
        bg: 'bg-surface-900',
        text: 'text-surface-300',
        border: 'border-surface-700',
        badge: 'bg-surface-800 text-surface-300 border border-surface-700',
        glow: '',
        color: '#94a3b8'
      };
  }
}

export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
}

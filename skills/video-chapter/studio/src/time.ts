export const formatClock = (seconds: number, withFrames = false, fps = 30) => {
  const safe = Math.max(0, Number.isFinite(seconds) ? seconds : 0);
  const whole = Math.floor(safe);
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  const secs = whole % 60;
  const base = hours
    ? `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
    : `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  if (!withFrames) return base;
  const frames = Math.floor((safe - whole) * fps);
  return `${base}:${String(frames).padStart(2, '0')}`;
};

export const parseClock = (value: string) => {
  const parts = value.trim().split(':').map(Number);
  if (parts.some((part) => !Number.isFinite(part) || part < 0)) return null;
  if (parts.length === 2 && parts[1] < 60) {
    return parts[0] * 60 + parts[1];
  }
  if (parts.length === 3 && parts[1] < 60 && parts[2] < 60) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  }
  return null;
};


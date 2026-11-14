// Мост к Electron (preload кладёт window.desktop). В браузере — заглушки.
export const desktop = typeof window !== "undefined" ? window.desktop : undefined;
export const isDesktop = !!desktop;

export const windowControls = {
  minimize: () => desktop?.minimize(),
  toggleMaximize: () => desktop?.toggleMaximize(),
  close: () => desktop?.close(),
  onMaximizeChange: (fn) => desktop?.onMaximizeChange?.(fn) || (() => {}),
  isMaximized: () => desktop?.isMaximized?.() ?? Promise.resolve(false),
};

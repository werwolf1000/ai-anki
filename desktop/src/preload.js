const { contextBridge, ipcRenderer } = require("electron");

// window.desktop — признак десктоп-режима для React-приложения + управление frameless-окном
contextBridge.exposeInMainWorld("desktop", {
  platform: process.platform,
  minimize: () => ipcRenderer.send("win:minimize"),
  toggleMaximize: () => ipcRenderer.send("win:toggle-maximize"),
  close: () => ipcRenderer.send("win:close"),
  isMaximized: () => ipcRenderer.invoke("win:is-maximized"),
  version: () => ipcRenderer.invoke("app:version"),
  onMaximizeChange: (cb) => {
    const listener = (_e, value) => cb(value);
    ipcRenderer.on("win:maximized", listener);
    return () => ipcRenderer.removeListener("win:maximized", listener);
  },
});

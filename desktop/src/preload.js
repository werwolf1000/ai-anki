const { contextBridge, ipcRenderer } = require("electron");

// window.desktop — признак десктоп-режима для React-приложения + управление frameless-окном
contextBridge.exposeInMainWorld("desktop", {
  platform: process.platform,
  minimize: () => ipcRenderer.send("win:minimize"),
  toggleMaximize: () => ipcRenderer.send("win:toggle-maximize"),
  close: () => ipcRenderer.send("win:close"),
  isMaximized: () => ipcRenderer.invoke("win:is-maximized"),
  version: () => ipcRenderer.invoke("app:version"),
  // локальная модель на этом компьютере (Strata и др.) — мост к серверу AI Anki
  bridge: {
    get: () => ipcRenderer.invoke("bridge:get"),
    set: (patch) => ipcRenderer.invoke("bridge:set", patch),
    auth: (auth) => ipcRenderer.invoke("bridge:auth", auth),
    test: () => ipcRenderer.invoke("bridge:test"),
    onState: (cb) => {
      const listener = (_e, st) => cb(st);
      ipcRenderer.on("bridge:state", listener);
      return () => ipcRenderer.removeListener("bridge:state", listener);
    },
  },
  onMaximizeChange: (cb) => {
    const listener = (_e, value) => cb(value);
    ipcRenderer.on("win:maximized", listener);
    return () => ipcRenderer.removeListener("win:maximized", listener);
  },
});

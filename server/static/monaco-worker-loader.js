"use strict";

var params = new URL(self.location.href).searchParams;
var label = params.get("label") || "editor";
var baseParam = params.get("base") || "/static/vendor/monaco";
var baseUrl = baseParam.indexOf("://") >= 0 ? baseParam : self.location.origin + baseParam;

self.MonacoEnvironment = { baseUrl: baseUrl };

var scripts = {
  typescript: baseUrl + "/language/typescript/tsWorker.js",
  javascript: baseUrl + "/language/typescript/tsWorker.js",
  json: baseUrl + "/language/json/jsonWorker.js",
  css: baseUrl + "/language/css/cssWorker.js",
  html: baseUrl + "/language/html/htmlWorker.js",
  editor: baseUrl + "/base/worker/workerMain.js",
};

var script = scripts[label] || scripts.editor;
importScripts(script);

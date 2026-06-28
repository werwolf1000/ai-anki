"use strict";

var params = new URL(self.location.href).searchParams;
var baseParam = params.get("base") || "/static/vendor/monaco";
var baseUrl = baseParam.indexOf("://") >= 0 ? baseParam : self.location.origin + baseParam;

self.MonacoEnvironment = { baseUrl: baseUrl };
importScripts(baseUrl + "/base/worker/workerMain.js");

"use strict";

var params = new URL(self.location.href).searchParams;
var vsParam = params.get("vs") || "/static/vendor/vs";
var vsUrl = vsParam.indexOf("://") >= 0 ? vsParam : self.location.origin + vsParam;
var baseUrl = vsUrl.replace(/\/vs\/?$/, "") || vsUrl.substring(0, vsUrl.lastIndexOf("/"));

self.MonacoEnvironment = { baseUrl: baseUrl };
importScripts(vsUrl + "/base/worker/workerMain.js");

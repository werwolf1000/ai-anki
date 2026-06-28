(() => {
  const CDN_VS = "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs";
  const LOCAL_VS = "/static/vendor/vs";

  let editor = null;
  let initPromise = null;
  let vsBase = CDN_VS;

  function mapLanguage(lang) {
    const l = (lang || "typescript").toLowerCase();
    const m = {
      typescript: "typescript",
      ts: "typescript",
      javascript: "javascript",
      js: "javascript",
      python: "python",
      py: "python",
      php: "php",
      html: "html",
      css: "css",
      json: "json",
      sql: "sql",
      shell: "shell",
      bash: "shell",
    };
    return m[l] || "plaintext";
  }

  function workerLabelKey(label) {
    if (label === "typescript" || label === "javascript") return "typescript";
    if (label === "json") return "json";
    if (label === "css" || label === "scss" || label === "less") return "css";
    if (label === "html" || label === "handlebars" || label === "razor") return "html";
    return "editor";
  }

  function workerLoaderUrl() {
    return `/static/monaco-worker-loader.js?v=8&vs=${encodeURIComponent(vsBase)}`;
  }

  function monacoBaseUrl(vsPath) {
    return vsPath.replace(/\/vs\/?$/, "") || vsPath.substring(0, vsPath.lastIndexOf("/"));
  }

  function configureMonacoEnv(base) {
    vsBase = base;
    window.MonacoEnvironment = {
      baseUrl: monacoBaseUrl(base),
      getWorker(_workerId, label) {
        return new Worker(workerLoaderUrl(), { name: workerLabelKey(label) });
      },
    };
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = () => resolve();
      s.onerror = () => reject(new Error(`Failed to load ${src}`));
      document.head.appendChild(s);
    });
  }

  async function resolveVsBase() {
    try {
      const r = await fetch(`${LOCAL_VS}/loader.js`, { method: "HEAD" });
      if (r.ok) return LOCAL_VS;
    } catch (_) {
      /* CDN fallback */
    }
    return CDN_VS;
  }

  const ANGULAR_EXTRA_LIBS = [
    {
      path: "file:///node_modules/@angular/core/index.d.ts",
      content: `
declare module '@angular/core' {
  export function Component(metadata: {
    selector?: string;
    standalone?: boolean;
    imports?: unknown[];
    template?: string;
    templateUrl?: string;
    styles?: string[];
    styleUrls?: string[];
    providers?: unknown[];
    changeDetection?: number;
  }): ClassDecorator;
  export function Injectable(metadata?: { providedIn?: 'root' | null | undefined }): ClassDecorator;
  export function Input(alias?: string): PropertyDecorator;
  export function Output(alias?: string): PropertyDecorator;
  export function Pipe(metadata: { name: string; standalone?: boolean }): ClassDecorator;
  export function Directive(metadata: { selector: string; standalone?: boolean }): ClassDecorator;
  export class EventEmitter<T = unknown> {
    emit(value?: T): void;
    subscribe(fn: (value: T) => void): { unsubscribe(): void };
  }
  export function inject<T>(token: unknown): T;
  export function signal<T>(initial: T): {
    (): T;
    set(value: T): void;
    update(fn: (value: T) => T): void;
  };
  export function computed<T>(fn: () => T): () => T;
  export function effect(fn: () => void): void;
  export function input<T>(): () => T;
  export function input<T>(options: { required?: boolean }): () => T;
  export function output<T = void>(): { emit(value?: T): void };
  export interface OnInit { ngOnInit(): void | Promise<void>; }
  export interface OnDestroy { ngOnDestroy(): void; }
  export enum ChangeDetectionStrategy { OnPush = 0, Default = 1 }
}
`,
    },
    {
      path: "file:///node_modules/@angular/common/index.d.ts",
      content: `
declare module '@angular/common' {
  export class CommonModule {}
  export class NgIf {}
  export class NgFor {}
  export class NgClass {}
  export class NgStyle {}
  export class AsyncPipe {}
  export class NgOptimizedImage {}
  export class NgTemplateOutlet {}
}
`,
    },
    {
      path: "file:///node_modules/@angular/forms/index.d.ts",
      content: `
declare module '@angular/forms' {
  export class FormsModule {}
  export class ReactiveFormsModule {}
  export class FormBuilder {
    group(controls: Record<string, unknown>): FormGroup;
  }
  export class FormControl<T = unknown> {
    constructor(value?: T, opts?: unknown);
    value: T;
  }
  export class FormGroup {
    invalid: boolean;
    value: Record<string, unknown>;
  }
  export class Validators {
    static required: unknown;
    static email: unknown;
    static minLength(min: number): unknown;
  }
  export const NG_VALUE_ACCESSOR: unknown;
}
`,
    },
    {
      path: "file:///node_modules/@angular/router/index.d.ts",
      content: `
declare module '@angular/router' {
  export type Routes = Route[];
  export interface Route {
    path?: string;
    component?: unknown;
    loadComponent?: () => Promise<unknown>;
    redirectTo?: string;
    pathMatch?: 'full' | 'prefix';
    canActivate?: unknown[];
  }
  export function provideRouter(routes: Routes): unknown;
  export type CanActivateFn = () => boolean | Promise<boolean> | unknown;
  export type CanDeactivateFn<T = unknown> = (component: T) => boolean | Promise<boolean>;
  export type ResolveFn<T = unknown> = (route: unknown) => T | Promise<T>;
  export class RouterLink {}
  export class RouterLinkActive {}
  export class ActivatedRoute {
    paramMap: { get(name: string): string | null };
  }
}
`,
    },
    {
      path: "file:///node_modules/@angular/common/http/index.d.ts",
      content: `
declare module '@angular/common/http' {
  export class HttpClient {
    get<T>(url: string): import('rxjs').Observable<T>;
    post<T>(url: string, body: unknown): import('rxjs').Observable<T>;
  }
  export function provideHttpClient(): unknown;
  export type HttpInterceptorFn = (req: unknown, next: (req: unknown) => unknown) => unknown;
}
`,
    },
    {
      path: "file:///node_modules/@angular/platform-browser/index.d.ts",
      content: `
declare module '@angular/platform-browser' {
  export function bootstrapApplication(component: unknown, options?: { providers?: unknown[] }): unknown;
}
`,
    },
    {
      path: "file:///node_modules/rxjs/index.d.ts",
      content: `
declare module 'rxjs' {
  export class Observable<T> {
    pipe(...operations: unknown[]): Observable<unknown>;
    subscribe(observer?: unknown): { unsubscribe(): void };
  }
  export function of<T>(...values: T[]): Observable<T>;
  export function map<T, R>(project: (value: T) => R): unknown;
  export function switchMap<T, R>(project: (value: T) => Observable<R>): unknown;
  export function debounceTime<T>(ms: number): unknown;
  export function distinctUntilChanged<T>(): unknown;
}
`,
    },
  ];

  function configureLanguageServices() {
    const tsDefaults = monaco.languages.typescript.typescriptDefaults;
    const jsDefaults = monaco.languages.typescript.javascriptDefaults;
    const compilerOptions = {
      target: monaco.languages.typescript.ScriptTarget.ES2020,
      module: monaco.languages.typescript.ModuleKind.ESNext,
      moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
      allowNonTsExtensions: true,
      allowJs: true,
      checkJs: false,
      noEmit: true,
      esModuleInterop: true,
      jsx: monaco.languages.typescript.JsxEmit.React,
      strict: false,
    };

    tsDefaults.setCompilerOptions(compilerOptions);
    jsDefaults.setCompilerOptions(compilerOptions);
    tsDefaults.setDiagnosticsOptions({
      noSemanticValidation: false,
      noSyntaxValidation: false,
    });
    jsDefaults.setDiagnosticsOptions({
      noSemanticValidation: false,
      noSyntaxValidation: false,
    });
    tsDefaults.setEagerModelSync(true);
    jsDefaults.setEagerModelSync(true);

    for (const lib of ANGULAR_EXTRA_LIBS) {
      tsDefaults.addExtraLib(lib.content, lib.path);
      jsDefaults.addExtraLib(lib.content, lib.path);
    }
  }

  function setEditorModel(language) {
    const lang = mapLanguage(language);
    const ext = lang === "typescript" ? "ts" : lang === "javascript" ? "js" : lang;
    const uri = monaco.Uri.parse(`inmemory://ai-anki/card.${ext}`);
    const value = editor.getValue();
    const oldModel = editor.getModel();
    const model = monaco.editor.getModel(uri) || monaco.editor.createModel(value, lang, uri);
    if (model !== oldModel) {
      model.setValue(value);
      monaco.editor.setModelLanguage(model, lang);
      editor.setModel(model);
      if (oldModel && oldModel !== model) oldModel.dispose();
    } else {
      monaco.editor.setModelLanguage(model, lang);
    }
  }

  async function ensureEditor() {
    if (editor) return editor;
    if (initPromise) return initPromise;

    initPromise = (async () => {
      const base = await resolveVsBase();
      configureMonacoEnv(base);
      await loadScript(`${base}/loader.js`);
      await new Promise((resolve, reject) => {
        window.require.config({ paths: { vs: base } });
        window.require(["vs/editor/editor.main"], resolve, reject);
      });

      configureLanguageServices();

      const host = document.getElementById("code-editor-host");
      editor = monaco.editor.create(host, {
        value: "",
        language: "typescript",
        theme: "vs",
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 14,
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        lineNumbers: "on",
        tabSize: 2,
        insertSpaces: true,
        wordWrap: "off",
        scrollBeyondLastLine: false,
        padding: { top: 8, bottom: 8 },
        suggestOnTriggerCharacters: true,
        quickSuggestions: { other: true, comments: false, strings: true },
        wordBasedSuggestions: "currentDocument",
        tabCompletion: "on",
        acceptSuggestionOnEnter: "on",
        parameterHints: { enabled: true },
        suggest: {
          preview: true,
          showKeywords: true,
          showSnippets: true,
          showClasses: true,
          showFunctions: true,
          showVariables: true,
          showModules: true,
          showProperties: true,
          showMethods: true,
          showInterfaces: true,
          showTypes: true,
        },
        renderLineHighlight: "all",
        scrollbar: { verticalScrollbarSize: 10, horizontalScrollbarSize: 10 },
      });

      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
        host.dispatchEvent(new CustomEvent("code-submit", { bubbles: true }));
      });

      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Space, () => {
        editor.trigger("keyboard", "editor.action.triggerSuggest", {});
      });

      return editor;
    })();

    return initPromise;
  }

  window.CodeEditor = {
    async show(language) {
      const host = document.getElementById("code-editor-host");
      host.classList.remove("hidden");
      await ensureEditor();
      setEditorModel(language);
      editor.layout();
      editor.focus();
    },

    hide() {
      document.getElementById("code-editor-host").classList.add("hidden");
    },

    getValue() {
      return editor ? editor.getValue() : "";
    },

    clear() {
      if (editor) editor.setValue("");
    },

    layout() {
      if (editor) editor.layout();
    },
  };
})();

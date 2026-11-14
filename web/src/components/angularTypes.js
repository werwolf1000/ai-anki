// Упрощённые типы Angular/RxJS для автодополнения в Monaco.
export const ANGULAR_LIBS = [
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

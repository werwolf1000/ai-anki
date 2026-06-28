#!/usr/bin/env python3
"""Generate Angular Live-coding deck (write code from scratch)."""
from __future__ import annotations

import json
from pathlib import Path


def live(q: str, task: str, ref: str, *, lang: str = "typescript") -> dict:
    return {
        "card_type": "live_code",
        "question": q,
        "task": task,
        "reference": ref.strip(),
        "language": lang,
    }


def build_cards() -> list[dict]:
    return [
        live(
            "Standalone-компонент приветствия",
            "Создай standalone-компонент GreetingComponent: selector app-greeting, шаблон с @Input() name и текст «Hello, {{ name }}!».",
            """import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-greeting',
  standalone: true,
  template: `<p>Hello, {{ name }}!</p>`,
})
export class GreetingComponent {
  @Input() name = 'World';
}""",
        ),
        live(
            "Сервис с providedIn root",
            "Напиши injectable-сервис CounterService с методами increment(): number и value(): number (внутренний счётчик).",
            """import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class CounterService {
  private count = 0;

  increment(): number {
    return ++this.count;
  }

  value(): number {
    return this.count;
  }
}""",
        ),
        live(
            "Двустороннее связывание",
            "Standalone-компонент с input [(ngModel)] для title и параграфом, выводящим title.",
            """import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-title-editor',
  standalone: true,
  imports: [FormsModule],
  template: `
    <input [(ngModel)]="title" />
    <p>{{ title }}</p>
  `,
})
export class TitleEditorComponent {
  title = '';
}""",
        ),
        live(
            "Reactive form — login",
            "Компонент с FormGroup: email (required), password (required, min 6). Кнопка submit disabled если form invalid.",
            """import { Component } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()">
      <input formControlName="email" />
      <input type="password" formControlName="password" />
      <button type="submit" [disabled]="form.invalid">Login</button>
    </form>
  `,
})
export class LoginComponent {
  form = this.fb.group({
    email: ['', Validators.required],
    password: ['', [Validators.required, Validators.minLength(6)]],
  });

  constructor(private fb: FormBuilder) {}

  submit() {}
}""",
        ),
        live(
            "HttpClient GET",
            "Сервис UserApi с методом getUsers(): Observable<User[]> через HttpClient GET /api/users.",
            """import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface User {
  id: number;
  name: string;
}

@Injectable({ providedIn: 'root' })
export class UserApi {
  private http = inject(HttpClient);

  getUsers() {
    return this.http.get<User[]>('/api/users');
  }
}""",
        ),
        live(
            "Async pipe в шаблоне",
            "Standalone UsersListComponent: users$ из UserApi, шаблон @for по users$ | async.",
            """import { Component, inject } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { UserApi } from './user-api';

@Component({
  selector: 'app-users-list',
  standalone: true,
  imports: [AsyncPipe],
  template: `
    @for (user of users$ | async; track user.id) {
      <p>{{ user.name }}</p>
    }
  `,
})
export class UsersListComponent {
  private api = inject(UserApi);
  users$ = this.api.getUsers();
}""",
        ),
        live(
            "Output EventEmitter",
            "Дочерний компонент Rating с @Output() rated = new EventEmitter<number>() и кнопками 1–5.",
            """import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'app-rating',
  standalone: true,
  template: `
    @for (n of [1, 2, 3, 4, 5]; track n) {
      <button type="button" (click)="pick(n)">{{ n }}</button>
    }
  `,
})
export class RatingComponent {
  @Output() rated = new EventEmitter<number>();

  pick(value: number) {
    this.rated.emit(value);
  }
}""",
        ),
        live(
            "RouterLink и RouterLinkActive",
            "NavComponent: ссылки /home и /about с routerLinkActive=\"active\".",
            """import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-nav',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  template: `
    <a routerLink="/home" routerLinkActive="active">Home</a>
    <a routerLink="/about" routerLinkActive="active">About</a>
  `,
})
export class NavComponent {}""",
        ),
        live(
            "Lazy load standalone route",
            "Маршрут path 'admin' с loadComponent для AdminPage.",
            """import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'admin',
    loadComponent: () => import('./admin/admin.page').then(m => m.AdminPage),
  },
];""",
        ),
        live(
            "Route guard CanActivateFn",
            "Функция authGuard: inject AuthService, return router.parseUrl('/login') если !isLoggedIn(), иначе true.",
            """import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.isLoggedIn() ? true : router.parseUrl('/login');
};""",
        ),
        live(
            "Signal counter",
            "CounterComponent: signal count, кнопка increment через count.update.",
            """import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-counter',
  standalone: true,
  template: `
    <p>{{ count() }}</p>
    <button type="button" (click)="increment()">+</button>
  `,
})
export class CounterComponent {
  count = signal(0);

  increment() {
    this.count.update(v => v + 1);
  }
}""",
        ),
        live(
            "computed signal",
            "Компонент с signal items: string[] и computed totalLength — сумма длин строк.",
            """import { Component, computed, signal } from '@angular/core';

@Component({
  selector: 'app-stats',
  standalone: true,
  template: `<p>Total: {{ totalLength() }}</p>`,
})
export class StatsComponent {
  items = signal(['a', 'bb', 'ccc']);
  totalLength = computed(() => this.items().reduce((sum, s) => sum + s.length, 0));
}""",
        ),
        live(
            "effect для логирования",
            "Комponent с signal query и effect в constructor, который console.log при изменении query.",
            """import { Component, effect, signal } from '@angular/core';

@Component({
  selector: 'app-search-log',
  standalone: true,
  template: `<input [value]="query()" (input)="onInput($event)" />`,
})
export class SearchLogComponent {
  query = signal('');

  constructor() {
    effect(() => console.log('query:', this.query()));
  }

  onInput(event: Event) {
    this.query.set((event.target as HTMLInputElement).value);
  }
}""",
        ),
        live(
            "Pure pipe uppercase truncate",
            "Pipe truncate с @Pipe name truncate, transform(value: string, limit = 20): string.",
            """import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'truncate', standalone: true })
export class TruncatePipe implements PipeTransform {
  transform(value: string, limit = 20): string {
    if (!value) return '';
    return value.length <= limit ? value : value.slice(0, limit) + '…';
  }
}""",
        ),
        live(
            "Custom directive — highlight",
            "Директива appHighlight: @HostBinding('style.backgroundColor') yellow при hover.",
            """import { Directive, HostBinding, HostListener } from '@angular/core';

@Directive({
  selector: '[appHighlight]',
  standalone: true,
})
export class HighlightDirective {
  @HostBinding('style.backgroundColor') bg = '';

  @HostListener('mouseenter')
  onEnter() {
    this.bg = 'yellow';
  }

  @HostListener('mouseleave')
  onLeave() {
    this.bg = '';
  }
}""",
        ),
        live(
            "ControlValueAccessor — toggle",
            "Минимальный ToggleComponent с NG_VALUE_ACCESSOR, writeValue/registerOnChange, клик переключает boolean.",
            """import { Component, forwardRef } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'app-toggle',
  standalone: true,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => ToggleComponent),
    multi: true,
  }],
  template: `<button type="button" (click)="toggle()">{{ on ? 'ON' : 'OFF' }}</button>`,
})
export class ToggleComponent implements ControlValueAccessor {
  on = false;
  private onChange: (v: boolean) => void = () => {};

  writeValue(value: boolean): void {
    this.on = !!value;
  }

  registerOnChange(fn: (v: boolean) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(_fn: () => void): void {}

  toggle() {
    this.on = !this.on;
    this.onChange(this.on);
  }
}""",
        ),
        live(
            "HttpInterceptor — auth header",
            "interceptor authInterceptor: clone request с Authorization Bearer token из AuthService.",
            """import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).token();
  if (!token) return next(req);
  return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};""",
        ),
        live(
            "Resolver для данных роута",
            "userResolver: inject UserApi, return getUserById(route.paramMap.get('id')!).",
            """import { inject } from '@angular/core';
import { ResolveFn } from '@angular/router';
import { UserApi, User } from './user-api';

export const userResolver: ResolveFn<User> = route => {
  const id = route.paramMap.get('id')!;
  return inject(UserApi).getUserById(id);
};""",
        ),
        live(
            "@defer блок",
            "Шаблон с @defer (on viewport) для тяжёлого HeavyChartComponent и @placeholder «Loading…».",
            """import { Component } from '@angular/core';
import { HeavyChartComponent } from './heavy-chart.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [HeavyChartComponent],
  template: `
    @defer (on viewport) {
      <app-heavy-chart />
    } @placeholder {
      <p>Loading…</p>
    }
  `,
})
export class DashboardComponent {}""",
        ),
        live(
            "inject() в field initializer",
            "Комponent использует private api = inject(ProductApi) без constructor DI.",
            """import { Component, inject } from '@angular/core';
import { ProductApi } from './product-api';

@Component({
  selector: 'app-products',
  standalone: true,
  template: `@for (p of api.list(); track p.id) { <p>{{ p.name }}</p> }`,
})
export class ProductsComponent {
  protected api = inject(ProductApi);
}""",
        ),
        live(
            "Model input (Angular 17+)",
            "Комponent с input.required<string>() для title и шаблоном h1.",
            """import { Component, input } from '@angular/core';

@Component({
  selector: 'app-heading',
  standalone: true,
  template: `<h1>{{ title() }}</h1>`,
})
export class HeadingComponent {
  title = input.required<string>();
}""",
        ),
        live(
            "output() function",
            "Child с output<number>() saved и кнопка emit(42).",
            """import { Component, output } from '@angular/core';

@Component({
  selector: 'app-save-btn',
  standalone: true,
  template: `<button type="button" (click)="save.emit(42)">Save</button>`,
})
export class SaveBtnComponent {
  save = output<number>();
}""",
        ),
        live(
            "FormControl в standalone",
            "Reactive field search: FormControl default '', input [formControl] и valueChanges subscribe в ngOnInit.",
            """import { Component, OnInit, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { debounceTime } from 'rxjs';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `<input [formControl]="search" placeholder="Search" />`,
})
export class SearchComponent implements OnInit {
  search = new FormControl('', { nonNullable: true });

  ngOnInit() {
    this.search.valueChanges.pipe(debounceTime(300)).subscribe(v => console.log(v));
  }
}""",
        ),
        live(
            "switchMap поиск",
            "SearchService.search(term): Observable<Item[]> — в компоненте search.valueChanges pipe switchMap к search.",
            """import { Component, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { AsyncPipe } from '@angular/common';
import { switchMap, debounceTime, distinctUntilChanged } from 'rxjs';
import { SearchService } from './search.service';

@Component({
  selector: 'app-live-search',
  standalone: true,
  imports: [ReactiveFormsModule, AsyncPipe],
  template: `
    <input [formControl]="q" />
    @for (item of results$ | async; track item.id) {
      <div>{{ item.name }}</div>
    }
  `,
})
export class LiveSearchComponent {
  private search = inject(SearchService);
  q = new FormControl('', { nonNullable: true });
  results$ = this.q.valueChanges.pipe(
    debounceTime(300),
    distinctUntilChanged(),
    switchMap(term => this.search.search(term)),
  );
}""",
        ),
        live(
            "NgOptimizedImage",
            "Комponent с NgOptimizedImage, img ngSrc=\"/hero.jpg\" width height priority.",
            """import { Component } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';

@Component({
  selector: 'app-hero',
  standalone: true,
  imports: [NgOptimizedImage],
  template: `
    <img ngSrc="/hero.jpg" width="800" height="400" priority alt="Hero" />
  `,
})
export class HeroComponent {}""",
        ),
        live(
            "TrackBy функция",
            "Комponent *ngFor trackById для items с id (class Item { id, name }).",
            """import { Component } from '@angular/core';
import { NgFor } from '@angular/common';

interface Item {
  id: number;
  name: string;
}

@Component({
  selector: 'app-list',
  standalone: true,
  imports: [NgFor],
  template: `
    <div *ngFor="let item of items; trackBy: trackById">{{ item.name }}</div>
  `,
})
export class ListComponent {
  items: Item[] = [];

  trackById(_index: number, item: Item) {
    return item.id;
  }
}""",
        ),
        live(
            "HostListener document:keydown",
            "Комponent слушает @HostListener('document:keydown.escape') и закрывает modal flag.",
            """import { Component, HostListener, signal } from '@angular/core';

@Component({
  selector: 'app-modal',
  standalone: true,
  template: `
    @if (open()) {
      <div class="modal">Press Esc to close</div>
    }
  `,
})
export class ModalComponent {
  open = signal(true);

  @HostListener('document:keydown.escape')
  onEsc() {
    this.open.set(false);
  }
}""",
        ),
        live(
            "Content projection ng-content",
            "CardComponent с ng-content select=\"[card-title]\" и default ng-content.",
            """import { Component } from '@angular/core';

@Component({
  selector: 'app-card',
  standalone: true,
  template: `
    <header><ng-content select="[card-title]"></ng-content></header>
    <section><ng-content></ng-content></section>
  `,
})
export class CardComponent {}""",
        ),
        live(
            "ng-template ngTemplateOutlet",
            "Parent с TemplateRef #tpl и ngTemplateOutlet с context { $implicit: name }.",
            """import { Component } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';

@Component({
  selector: 'app-parent',
  standalone: true,
  imports: [NgTemplateOutlet],
  template: `
    <ng-template #hello let-name>
      <p>Hi, {{ name }}</p>
    </ng-template>
    <ng-container *ngTemplateOutlet="hello; context: { $implicit: 'Anna' }" />
  `,
})
export class ParentComponent {}""",
        ),
        live(
            "CanDeactivate guard",
            "canDeactivate: если form.dirty — confirm('Leave?').",
            """import { CanDeactivateFn } from '@angular/router';

export interface HasDirtyForm {
  isDirty(): boolean;
}

export const dirtyFormGuard: CanDeactivateFn<HasDirtyForm> = component => {
  if (!component.isDirty()) return true;
  return confirm('Leave without saving?');
};""",
        ),
        live(
            "MatDialog open (conceptual)",
            "Сервис DialogService openConfirm(): Observable<boolean> — open ConfirmDialogComponent, afterClosed.",
            """import { Injectable, inject } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ConfirmDialogComponent } from './confirm-dialog.component';

@Injectable({ providedIn: 'root' })
export class DialogService {
  private dialog = inject(MatDialog);

  openConfirm(message: string) {
    return this.dialog
      .open(ConfirmDialogComponent, { data: { message } })
      .afterClosed();
  }
}""",
        ),
        live(
            "Signal input + OnPush",
            "ChangeDetection OnPush component с input signal user и @if (user()) show email.",
            """import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'app-user-chip',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (user(); as u) {
      <span>{{ u.email }}</span>
    }
  `,
})
export class UserChipComponent {
  user = input<{ email: string } | null>(null);
}""",
        ),
        live(
            "Resource API (Angular 19 concept)",
            "Псевдо: rxResource или signal + toSignal(http.get) для products.",
            """import { Component, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { toSignal } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-product-grid',
  standalone: true,
  template: `@for (p of products(); track p.id) { <article>{{ p.name }}</article> }`,
})
export class ProductGridComponent {
  private http = inject(HttpClient);
  products = toSignal(this.http.get<Product[]>('/api/products'), { initialValue: [] });
}

interface Product {
  id: number;
  name: string;
}""",
        ),
        live(
            "Standalone bootstrapApplication",
            "main.ts: bootstrapApplication(AppComponent, providers: [provideRouter(routes), provideHttpClient()]).",
            """import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';

bootstrapApplication(AppComponent, {
  providers: [provideRouter(routes), provideHttpClient()],
});""",
        ),
        live(
            "Functional ErrorHandler",
            "provideAppInitializer или ErrorHandler — class GlobalHandler implements ErrorHandler handleError console.error.",
            """import { ErrorHandler, Injectable } from '@angular/core';

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  handleError(error: unknown): void {
    console.error('Unhandled error:', error);
  }
}

// providers: [{ provide: ErrorHandler, useClass: GlobalErrorHandler }]""",
        ),
        live(
            "Route title и data",
            "Route с title: 'Products' и data: { animation: 'ProductsPage' }.",
            """import { Routes } from '@angular/router';
import { ProductsPage } from './products.page';

export const routes: Routes = [
  {
    path: 'products',
    component: ProductsPage,
    title: 'Products',
    data: { animation: 'ProductsPage' },
  },
];""",
        ),
        live(
            "ViewChild signal",
            "Component с viewChild.required<ElementRef>('box') и ngAfterViewInit log nativeElement.",
            """import { AfterViewInit, Component, ElementRef, viewChild } from '@angular/core';

@Component({
  selector: 'app-box-host',
  standalone: true,
  template: `<div #box>Box</div>`,
})
export class BoxHostComponent implements AfterViewInit {
  box = viewChild.required<ElementRef<HTMLElement>>('box');

  ngAfterViewInit() {
    console.log(this.box().nativeElement);
  }
}""",
        ),
        live(
            "DestroyRef + takeUntilDestroyed",
            "Component подписка interval pipe takeUntilDestroyed() без manual unsubscribe.",
            """import { Component, DestroyRef, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { interval } from 'rxjs';

@Component({
  selector: 'app-ticker',
  standalone: true,
  template: `<p>{{ tick }}</p>`,
})
export class TickerComponent {
  private destroyRef = inject(DestroyRef);
  tick = 0;

  constructor() {
    interval(1000)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(n => (this.tick = n));
  }
}""",
        ),
        live(
            "Validators.custom email",
            "ValidatorFn emailPattern: return { email: true } если нет @.",
            """import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export const simpleEmailValidator: ValidatorFn = (
  control: AbstractControl
): ValidationErrors | null => {
  const value = String(control.value ?? '');
  return value.includes('@') ? null : { email: true };
};""",
        ),
        live(
            "FormArray динамические телефоны",
            "FormBuilder group с FormArray phones, метод addPhone(), template @for control of phones.controls.",
            """import { Component } from '@angular/core';
import { FormArray, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-phones',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div [formGroup]="form">
      <div formArrayName="phones">
        @for (ctrl of phones.controls; track $index) {
          <input [formControlName]="$index" />
        }
      </div>
      <button type="button" (click)="addPhone()">Add</button>
    </div>
  `,
})
export class PhonesComponent {
  form = this.fb.group({ phones: this.fb.array([]) });

  constructor(private fb: FormBuilder) {
    this.addPhone();
  }

  get phones() {
    return this.form.get('phones') as FormArray;
  }

  addPhone() {
    this.phones.push(this.fb.control('', Validators.required));
  }
}""",
        ),
        live(
            "Pipe async + @let (Angular 18+)",
            "Шаблон @let user = users$ | async; @if (user) { ... }",
            """import { Component, inject } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { UserApi } from './user-api';

@Component({
  selector: 'app-profile-link',
  standalone: true,
  imports: [AsyncPipe],
  template: `
    @let user = users$ | async;
    @if (user) {
      <a [routerLink]="['/users', user.id]">{{ user.name }}</a>
    }
  `,
})
export class ProfileLinkComponent {
  users$ = inject(UserApi).getUsers();
}""",
        ),
        live(
            "Structural directive *ngIf else",
            "Шаблон *ngIf=\"loggedIn(); else guest\" с ng-template #guest.",
            """import { Component, signal } from '@angular/core';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-auth-banner',
  standalone: true,
  imports: [NgIf],
  template: `
    <div *ngIf="loggedIn(); else guest">Welcome back</div>
    <ng-template #guest><div>Please log in</div></ng-template>
  `,
})
export class AuthBannerComponent {
  loggedIn = signal(false);
}""",
        ),
        live(
            "Router outlet + child routes",
            "Parent с router-outlet и children routes path '' -> List, ':id' -> Detail.",
            """import { Routes } from '@angular/router';
import { ShellComponent } from './shell.component';

export const routes: Routes = [
  {
    path: 'items',
    component: ShellComponent,
    children: [
      { path: '', loadComponent: () => import('./list').then(m => m.ListComponent) },
      { path: ':id', loadComponent: () => import('./detail').then(m => m.DetailComponent) },
    ],
  },
];""",
        ),
        live(
            "Environment injection",
            "InjectionToken API_URL и useValue в providers из environment.apiUrl.",
            """import { InjectionToken, inject } from '@angular/core';

export const API_URL = new InjectionToken<string>('API_URL');

export class ApiClient {
  private base = inject(API_URL);

  url(path: string) {
    return `${this.base}${path}`;
  }
}

// providers: [{ provide: API_URL, useValue: environment.apiUrl }]""",
        ),
        live(
            "TestBed standalone component",
            "Минимальный spec: TestBed.configureTestingModule({ imports: [CounterComponent] }); createComponent; click increment.",
            """import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CounterComponent } from './counter.component';

describe('CounterComponent', () => {
  let fixture: ComponentFixture<CounterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [CounterComponent] }).compileComponents();
    fixture = TestBed.createComponent(CounterComponent);
    fixture.detectChanges();
  });

  it('increments', () => {
    fixture.nativeElement.querySelector('button').click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('1');
  });
});""",
        ),
    ]


def main() -> None:
    cards = build_cards()
    deck = {"name": "Angular Live-coding", "cards": cards}
    out = Path(__file__).with_name("angular-live-coding.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {len(cards)} live_code cards -> {out}")


if __name__ == "__main__":
    main()

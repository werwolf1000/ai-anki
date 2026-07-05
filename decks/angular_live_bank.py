"""Extra Angular/TypeScript live-coding cards for the Anki deck bank."""
from __future__ import annotations

from live_coding_card import live


def extra_cards() -> list[dict]:
    return [
        # ── Компоненты (1–15) ──
        live(
            "Standalone карточка с ng-content",
            "Создайте standalone-компонент CardComponent с selector app-card. "
            "В шаблоне используйте ng-content с select=\"[card-header]\" для заголовка "
            "и второй ng-content без select для основного содержимого. "
            "Компонент не должен содержать бизнес-логики — только разметку.",
            """import { Component } from '@angular/core';

@Component({
  selector: 'app-card',
  standalone: true,
  template: `
    <article class="card">
      <header><ng-content select="[card-header]"></ng-content></header>
      <div class="body"><ng-content></ng-content></div>
    </article>
  `,
})
export class CardComponent {}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["standalone: true", "Два слота ng-content", "Selector app-card"],
        ),
        live(
            "model() для двустороннего связывания",
            "Реализуйте standalone-компонент StarRatingComponent с selector app-star-rating. "
            "Используйте model<number>() для рейтинга от 1 до 5. "
            "В шаблоне выведите кнопки 1–5; клик обновляет модель через rating.set(n).",
            """import { Component, model } from '@angular/core';

@Component({
  selector: 'app-star-rating',
  standalone: true,
  template: `
    @for (n of [1, 2, 3, 4, 5]; track n) {
      <button type="button" [class.active]="n <= rating()" (click)="rating.set(n)">
        {{ n }}
      </button>
    }
  `,
})
export class StarRatingComponent {
  rating = model(0);
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["model() вместо @Input/@Output", "Standalone", "5 кнопок рейтинга"],
        ),
        live(
            "Host metadata в @Component",
            "Создайте BadgeComponent с host: { class: 'badge', '[attr.data-count]': 'count()' }. "
            "Используйте signal count с начальным значением 0 и кнопку increment. "
            "Шаблон выводит {{ count() }}.",
            """import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-badge',
  standalone: true,
  host: {
    class: 'badge',
    '[attr.data-count]': 'count()',
  },
  template: `
    <span>{{ count() }}</span>
    <button type="button" (click)="increment()">+</button>
  `,
})
export class BadgeComponent {
  count = signal(0);

  increment() {
    this.count.update(v => v + 1);
  }
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["host metadata", "signal count", "data-count атрибут"],
        ),
        live(
            "input() с transform функцией",
            "Создайте LabelComponent с input transform: label = input('', { transform: (v: string | number) => String(v).toUpperCase() }). "
            "Шаблон: <label>{{ label() }}</label>. Standalone, selector app-label.",
            """import { Component, input } from '@angular/core';

@Component({
  selector: 'app-label',
  standalone: true,
  template: `<label>{{ label() }}</label>`,
})
export class LabelComponent {
  label = input('', { transform: (v: string | number) => String(v).toUpperCase() });
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["input() с transform", "Uppercase преобразование", "Standalone"],
        ),
        live(
            "output() с typed payload",
            "Создайте FilePickerComponent: скрытый input type=file и кнопка «Выбрать». "
            "При change эмитьте output<File | null>() selected. "
            "Standalone, selector app-file-picker.",
            """import { Component, output } from '@angular/core';

@Component({
  selector: 'app-file-picker',
  standalone: true,
  template: `
    <input #fileInput type="file" hidden (change)="onChange($event)" />
    <button type="button" (click)="fileInput.click()">Выбрать</button>
  `,
})
export class FilePickerComponent {
  selected = output<File | null>();

  onChange(event: Event) {
    const input = event.target as HTMLInputElement;
    this.selected.emit(input.files?.[0] ?? null);
  }
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["output<File | null>()", "Hidden file input", "Standalone"],
        ),
        live(
            "OnPush с immutable обновлением",
            "Создайте TodoListComponent с changeDetection: OnPush. "
            "items = signal<Todo[]>([]), метод add(title) добавляет { id: Date.now(), title, done: false } "
            "через items.update и spread. Шаблон @for по items().",
            """import { ChangeDetectionStrategy, Component, signal } from '@angular/core';

interface Todo {
  id: number;
  title: string;
  done: boolean;
}

@Component({
  selector: 'app-todo-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @for (todo of items(); track todo.id) {
      <p>{{ todo.title }}</p>
    }
    <button type="button" (click)="add('New')">Add</button>
  `,
})
export class TodoListComponent {
  items = signal<Todo[]>([]);

  add(title: string) {
    this.items.update(list => [...list, { id: Date.now(), title, done: false }]);
  }
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["ChangeDetectionStrategy.OnPush", "signal + immutable update", "@for с track"],
        ),
        live(
            "ViewEncapsulation.None",
            "Создайте GlobalStylesComponent с encapsulation: ViewEncapsulation.None "
            "и styles: ['p { margin: 0; }']. Шаблон <p>Global</p>. Standalone.",
            """import { Component, ViewEncapsulation } from '@angular/core';

@Component({
  selector: 'app-global-styles',
  standalone: true,
  encapsulation: ViewEncapsulation.None,
  styles: ['p { margin: 0; }'],
  template: `<p>Global</p>`,
})
export class GlobalStylesComponent {}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["ViewEncapsulation.None", "Inline styles", "Standalone"],
        ),
        live(
            "ngOnInit загрузка данных",
            "Создайте ProfileComponent, inject ProfileService, в ngOnInit вызовите load(). "
            "profile = signal<Profile | null>(null). ProfileService.load() возвращает Observable<Profile>. "
            "Подпишитесь и установите profile через set.",
            """import { Component, OnInit, inject, signal } from '@angular/core';
import { ProfileService, Profile } from './profile.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  template: `@if (profile(); as p) { <h2>{{ p.name }}</h2> }`,
})
export class ProfileComponent implements OnInit {
  private api = inject(ProfileService);
  profile = signal<Profile | null>(null);

  ngOnInit() {
    this.api.load().subscribe(p => this.profile.set(p));
  }
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["ngOnInit", "inject()", "signal для profile"],
        ),
        live(
            "Компонент-обёртка с @Input alias",
            "Создайте IconComponent: @Input({ alias: 'iconName' }) name = 'home'. "
            "Шаблон <i [class]=\"'icon-' + name\"></i>. Standalone, selector app-icon.",
            """import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-icon',
  standalone: true,
  template: `<i [class]="'icon-' + name"></i>`,
})
export class IconComponent {
  @Input({ alias: 'iconName' }) name = 'home';
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["@Input с alias", "Default value", "Standalone"],
        ),
        live(
            "Dynamic import компонента",
            "Создайте LazyHostComponent: flag = signal(false), метод open() устанавливает true. "
            "В шаблоне @if (flag()) { @defer { <app-modal /> } }. "
            "Импортируйте ModalComponent в imports.",
            """import { Component, signal } from '@angular/core';
import { ModalComponent } from './modal.component';

@Component({
  selector: 'app-lazy-host',
  standalone: true,
  imports: [ModalComponent],
  template: `
    <button type="button" (click)="open()">Open</button>
    @if (openFlag()) {
      @defer {
        <app-modal />
      }
    }
  `,
})
export class LazyHostComponent {
  openFlag = signal(false);

  open() {
    this.openFlag.set(true);
  }
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["@defer в шаблоне", "signal flag", "ModalComponent import"],
        ),
        live(
            "Компонент с несколькими output",
            "Создайте DialogActionsComponent с output<void>() confirm и cancel. "
            "Две кнопки вызывают confirm.emit() и cancel.emit(). Standalone.",
            """import { Component, output } from '@angular/core';

@Component({
  selector: 'app-dialog-actions',
  standalone: true,
  template: `
    <button type="button" (click)="confirm.emit()">OK</button>
    <button type="button" (click)="cancel.emit()">Cancel</button>
  `,
})
export class DialogActionsComponent {
  confirm = output<void>();
  cancel = output<void>();
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["Два output<void>()", "Standalone", "Две кнопки"],
        ),
        live(
            "Компонент с inline template URL concept",
            "Создайте FooterComponent с template содержащим текущий год через getter year. "
            "Standalone, selector app-footer, шаблон <footer>&copy; {{ year }}</footer>.",
            """import { Component } from '@angular/core';

@Component({
  selector: 'app-footer',
  standalone: true,
  template: `<footer>&copy; {{ year }}</footer>`,
})
export class FooterComponent {
  get year() {
    return new Date().getFullYear();
  }
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["Getter year", "Inline template", "Standalone"],
        ),
        live(
            "Компонент с CSS host-context",
            "Создайте ChipComponent с styles: ':host { display: inline-block; } :host(.selected) { font-weight: bold; }'. "
            "Input selected через signal input<boolean>. HostBinding class selected.",
            """import { Component, input } from '@angular/core';

@Component({
  selector: 'app-chip',
  standalone: true,
  host: { '[class.selected]': 'selected()' },
  styles: [':host { display: inline-block; } :host(.selected) { font-weight: bold; }'],
  template: `<span>{{ label() }}</span>`,
})
export class ChipComponent {
  label = input('Chip');
  selected = input(false);
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["host class binding", "input() signals", ":host styles"],
        ),
        live(
            "Компонент с ng-content fallback",
            "Создайте PanelComponent: ng-content для body, если пусто — показать «No content». "
            "Используйте @if и флаг hasContent через ContentChild или простой ng-content с ng-template #empty.",
            """import { Component } from '@angular/core';

@Component({
  selector: 'app-panel',
  standalone: true,
  template: `
    <section class="panel">
      <ng-content></ng-content>
    </section>
  `,
})
export class PanelComponent {}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["ng-content", "Standalone", "Section wrapper"],
        ),
        live(
            "Компонент с exportAs",
            "Создайте SearchBoxComponent с exportAs: 'searchBox', FormControl search, "
            "метод clear() сбрасывает search. Standalone с ReactiveFormsModule.",
            """import { Component } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';

@Component({
  selector: 'app-search-box',
  standalone: true,
  exportAs: 'searchBox',
  imports: [ReactiveFormsModule],
  template: `
    <input [formControl]="search" />
    <button type="button" (click)="clear()">Clear</button>
  `,
})
export class SearchBoxComponent {
  search = new FormControl('', { nonNullable: true });

  clear() {
    this.search.reset('');
  }
}""",
            lang="typescript",
            topic="Компоненты",
            requirements=["exportAs: 'searchBox'", "FormControl", "Метод clear()"],
        ),

        # ── Директивы и шаблоны (16–30) ──
        live(
            "@if @else if @else цепочка",
            "Создайте StatusBannerComponent со signal status: 'ok' | 'warn' | 'error'. "
            "В шаблоне используйте @if / @else if / @else для трёх разных сообщений. "
            "Кнопки меняют status через set.",
            """import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-status-banner',
  standalone: true,
  template: `
    @if (status() === 'ok') {
      <p class="ok">All good</p>
    } @else if (status() === 'warn') {
      <p class="warn">Warning</p>
    } @else {
      <p class="error">Error</p>
    }
    <button (click)="status.set('ok')">OK</button>
    <button (click)="status.set('warn')">Warn</button>
    <button (click)="status.set('error')">Error</button>
  `,
})
export class StatusBannerComponent {
  status = signal<'ok' | 'warn' | 'error'>('ok');
}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["@if @else if @else", "signal union type", "Три кнопки"],
        ),
        live(
            "@for с @empty блоком",
            "Создайте TagsComponent: tags = signal<string[]>([]). "
            "Шаблон @for (tag of tags(); track tag) с @empty «No tags». "
            "Кнопка add() добавляет 'tag-N'.",
            """import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-tags',
  standalone: true,
  template: `
    @for (tag of tags(); track tag) {
      <span>{{ tag }}</span>
    } @empty {
      <p>No tags</p>
    }
    <button type="button" (click)="add()">Add</button>
  `,
})
export class TagsComponent {
  tags = signal<string[]>([]);
  private n = 0;

  add() {
    this.n++;
    this.tags.update(t => [...t, `tag-${this.n}`]);
  }
}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["@for с track", "@empty блок", "signal tags"],
        ),
        live(
            "@switch @case @default",
            "Создайте ThemeSwitcherComponent: theme = signal<'light' | 'dark' | 'system'>('light'). "
            "Шаблон @switch (theme()) с @case для каждой темы и @default.",
            """import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-theme-switcher',
  standalone: true,
  template: `
    @switch (theme()) {
      @case ('light') { <p>Light mode</p> }
      @case ('dark') { <p>Dark mode</p> }
      @case ('system') { <p>System mode</p> }
      @default { <p>Unknown</p> }
    }
  `,
})
export class ThemeSwitcherComponent {
  theme = signal<'light' | 'dark' | 'system'>('light');
}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["@switch @case @default", "signal theme", "Standalone"],
        ),
        live(
            "@defer on idle",
            "Создайте HomeComponent с @defer (on idle) для HeavyWidgetComponent. "
            "@placeholder — «Waiting…». Импортируйте HeavyWidgetComponent.",
            """import { Component } from '@angular/core';
import { HeavyWidgetComponent } from './heavy-widget.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [HeavyWidgetComponent],
  template: `
    <h1>Home</h1>
    @defer (on idle) {
      <app-heavy-widget />
    } @placeholder {
      <p>Waiting…</p>
    }
  `,
})
export class HomeComponent {}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["@defer (on idle)", "@placeholder", "HeavyWidget import"],
        ),
        live(
            "@defer on interaction",
            "Создайте ChartHostComponent: @defer (on interaction) при клике на #trigger. "
            "Кнопка #trigger «Load chart», внутри defer — ChartComponent.",
            """import { Component } from '@angular/core';
import { ChartComponent } from './chart.component';

@Component({
  selector: 'app-chart-host',
  standalone: true,
  imports: [ChartComponent],
  template: `
    @defer (on interaction) {
      <app-chart />
    } @placeholder {
      <button #trigger type="button">Load chart</button>
    }
  `,
})
export class ChartHostComponent {}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["@defer (on interaction)", "#trigger placeholder", "ChartComponent"],
        ),
        live(
            "@defer on timer",
            "Создайте PromoComponent: @defer (on timer(2s)) для PromoBannerComponent. "
            "@loading (minimum 500ms) — spinner. @placeholder — «Soon».",
            """import { Component } from '@angular/core';
import { PromoBannerComponent } from './promo-banner.component';

@Component({
  selector: 'app-promo',
  standalone: true,
  imports: [PromoBannerComponent],
  template: `
    @defer (on timer(2s)) {
      <app-promo-banner />
    } @loading (minimum 500ms) {
      <p>Loading…</p>
    } @placeholder {
      <p>Soon</p>
    }
  `,
})
export class PromoComponent {}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["@defer (on timer(2s))", "@loading minimum", "@placeholder"],
        ),
        live(
            "@defer on viewport с @error",
            "Создайте FeedComponent: @defer (on viewport) для FeedListComponent. "
            "@error — «Failed to load». @placeholder — skeleton.",
            """import { Component } from '@angular/core';
import { FeedListComponent } from './feed-list.component';

@Component({
  selector: 'app-feed',
  standalone: true,
  imports: [FeedListComponent],
  template: `
    @defer (on viewport) {
      <app-feed-list />
    } @placeholder {
      <div class="skeleton">…</div>
    } @error {
      <p>Failed to load</p>
    }
  `,
})
export class FeedComponent {}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["@defer (on viewport)", "@error блок", "@placeholder skeleton"],
        ),
        live(
            "Директива appTooltip",
            "Создайте standalone-директиву TooltipDirective: selector [appTooltip], "
            "input appTooltip строка, @HostListener mouseenter/mouseleave показывает title.",
            """import { Directive, HostListener, input } from '@angular/core';

@Directive({
  selector: '[appTooltip]',
  standalone: true,
})
export class TooltipDirective {
  appTooltip = input('');

  @HostListener('mouseenter')
  onEnter() {
    // show tooltip with this.appTooltip()
  }

  @HostListener('mouseleave')
  onLeave() {
    // hide tooltip
  }
}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["Standalone directive", "input() для текста", "HostListener enter/leave"],
        ),
        live(
            "Директива autofocus",
            "Создайте AutofocusDirective: selector [appAutofocus], "
            "implements AfterViewInit, ngAfterViewInit вызывает nativeElement.focus().",
            """import { AfterViewInit, Directive, ElementRef, inject } from '@angular/core';

@Directive({
  selector: '[appAutofocus]',
  standalone: true,
})
export class AutofocusDirective implements AfterViewInit {
  private el = inject(ElementRef<HTMLElement>);

  ngAfterViewInit() {
    this.el.nativeElement.focus();
  }
}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["AfterViewInit", "inject(ElementRef)", "focus() в ngAfterViewInit"],
        ),
        live(
            "ClickOutside директива",
            "Создайте ClickOutsideDirective: output clickedOutside = output<void>(). "
            "@HostListener('document:click', ['$event']) — если клик вне элемента, emit.",
            """import { Directive, ElementRef, HostListener, inject, output } from '@angular/core';

@Directive({
  selector: '[appClickOutside]',
  standalone: true,
})
export class ClickOutsideDirective {
  private el = inject(ElementRef<HTMLElement>);
  clickedOutside = output<void>();

  @HostListener('document:click', ['$event'])
  onClick(event: MouseEvent) {
    if (!this.el.nativeElement.contains(event.target as Node)) {
      this.clickedOutside.emit();
    }
  }
}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["output<void>()", "document:click HostListener", "contains check"],
        ),
        live(
            "Structural directive *appRepeat",
            "Создайте RepeatDirective: selector [appRepeat], input appRepeatOf T[], "
            "ViewContainerRef создаёт embedded view для каждого элемента.",
            """import { Directive, Input, TemplateRef, ViewContainerRef, inject } from '@angular/core';

@Directive({
  selector: '[appRepeat]',
  standalone: true,
})
export class RepeatDirective<T> {
  private tpl = inject(TemplateRef<{ $implicit: T; index: number }>);
  private vcr = inject(ViewContainerRef);

  @Input() set appRepeatOf(items: T[] | null) {
    this.vcr.clear();
    (items ?? []).forEach((item, index) => {
      this.vcr.createEmbeddedView(this.tpl, { $implicit: item, index });
    });
  }
}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["TemplateRef + ViewContainerRef", "Input setter", "Generic T"],
        ),
        live(
            "ng-container без лишнего DOM",
            "Создайте SplitViewComponent: ng-container с @if для left/right панелей. "
            "active = signal<'left' | 'right'>('left'). Кнопки переключают.",
            """import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-split-view',
  standalone: true,
  template: `
    <ng-container>
      @if (active() === 'left') {
        <aside>Left panel</aside>
      } @else {
        <aside>Right panel</aside>
      }
    </ng-container>
    <button (click)="active.set('left')">Left</button>
    <button (click)="active.set('right')">Right</button>
  `,
})
export class SplitViewComponent {
  active = signal<'left' | 'right'>('left');
}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["ng-container", "@if внутри", "signal active"],
        ),
        live(
            "ngTemplateOutlet с context",
            "Создайте UserRowComponent: ng-template #row let-user, "
            "ngTemplateOutlet с context { $implicit: user, index: 0 }.",
            """import { Component } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';

@Component({
  selector: 'app-user-row',
  standalone: true,
  imports: [NgTemplateOutlet],
  template: `
    <ng-template #row let-user let-idx="index">
      <p>{{ idx }}: {{ user.name }}</p>
    </ng-template>
    <ng-container
      *ngTemplateOutlet="row; context: { $implicit: { name: 'Anna' }, index: 0 }"
    />
  `,
})
export class UserRowComponent {}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["NgTemplateOutlet", "context $implicit", "let-idx=\"index\""],
        ),
        live(
            "NgClass object syntax",
            "Создайте PillComponent: isActive, isDisabled — signals. "
            "[ngClass]=\"{ active: isActive(), disabled: isDisabled() }\".",
            """import { Component, signal } from '@angular/core';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-pill',
  standalone: true,
  imports: [NgClass],
  template: `<span [ngClass]="{ active: isActive(), disabled: isDisabled() }">Pill</span>`,
})
export class PillComponent {
  isActive = signal(true);
  isDisabled = signal(false);
}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["NgClass object", "signal bindings", "Standalone"],
        ),
        live(
            "NgStyle dynamic styles",
            "Создайте ProgressBarComponent: progress = signal(0). "
            "[ngStyle]=\"{ width: progress() + '%', background: progress() > 50 ? 'green' : 'orange' }\".",
            """import { Component, signal } from '@angular/core';
import { NgStyle } from '@angular/common';

@Component({
  selector: 'app-progress-bar',
  standalone: true,
  imports: [NgStyle],
  template: `<div [ngStyle]="{ width: progress() + '%', background: progress() > 50 ? 'green' : 'orange' }"></div>`,
})
export class ProgressBarComponent {
  progress = signal(35);
}""",
            lang="typescript",
            topic="Директивы и шаблоны",
            requirements=["NgStyle", "signal progress", "Условный background"],
        ),

        # ── Формы (31–45) ──
        live(
            "Typed Reactive FormGroup",
            "Создайте RegisterComponent с typed FormGroup через FormBuilder.group<{ email: string; age: number }>. "
            "Поля email (required) и age (min 18). Кнопка submit disabled при invalid.",
            """import { Component } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()">
      <input formControlName="email" />
      <input type="number" formControlName="age" />
      <button type="submit" [disabled]="form.invalid">Register</button>
    </form>
  `,
})
export class RegisterComponent {
  form = this.fb.nonNullable.group({
    email: ['', Validators.required],
    age: [0, [Validators.required, Validators.min(18)]],
  });

  constructor(private fb: FormBuilder) {}

  submit() {
    console.log(this.form.getRawValue());
  }
}""",
            lang="typescript",
            topic="Формы",
            requirements=["nonNullable.group", "Validators.required/min", "submit disabled"],
        ),
        live(
            "Cross-field validator password match",
            "Создайте passwordMatchValidator: ValidatorFn проверяет group.get('password') === group.get('confirm'). "
            "Примените к FormGroup в SignupComponent.",
            """import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export const passwordMatchValidator: ValidatorFn = (
  control: AbstractControl
): ValidationErrors | null => {
  const password = control.get('password')?.value;
  const confirm = control.get('confirm')?.value;
  return password === confirm ? null : { passwordMismatch: true };
};

// form = fb.group({ password: [''], confirm: [''] }, { validators: passwordMatchValidator })""",
            lang="typescript",
            topic="Формы",
            requirements=["ValidatorFn", "Group-level validator", "passwordMismatch error"],
        ),
        live(
            "Async validator unique email",
            "Создайте uniqueEmailValidator(api: UserApi): AsyncValidatorFn — "
            "return api.isEmailTaken(email) pipe map(taken => taken ? { taken: true } : null).",
            """import { AbstractControl, AsyncValidatorFn, ValidationErrors } from '@angular/forms';
import { inject } from '@angular/core';
import { map } from 'rxjs';
import { UserApi } from './user-api';

export function uniqueEmailValidator(): AsyncValidatorFn {
  const api = inject(UserApi);
  return (control: AbstractControl) =>
    api.isEmailTaken(String(control.value ?? '')).pipe(
      map(taken => (taken ? { emailTaken: true } : null) as ValidationErrors | null)
    );
}""",
            lang="typescript",
            topic="Формы",
            requirements=["AsyncValidatorFn", "inject(UserApi)", "map to ValidationErrors"],
        ),
        live(
            "FormArray removeAt",
            "Создайте SkillsComponent: FormArray skills, addSkill() push, removeSkill(i) removeAt. "
            "Template @for ctrl of skills.controls; track $index.",
            """import { Component } from '@angular/core';
import { FormArray, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-skills',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div [formGroup]="form">
      <div formArrayName="skills">
        @for (ctrl of skills.controls; track $index) {
          <input [formControlName]="$index" />
          <button type="button" (click)="removeSkill($index)">×</button>
        }
      </div>
      <button type="button" (click)="addSkill()">Add skill</button>
    </div>
  `,
})
export class SkillsComponent {
  form = this.fb.group({ skills: this.fb.array<string>([]) });

  constructor(private fb: FormBuilder) {}

  get skills() {
    return this.form.get('skills') as FormArray;
  }

  addSkill() {
    this.skills.push(this.fb.control('', Validators.required));
  }

  removeSkill(index: number) {
    this.skills.removeAt(index);
  }
}""",
            lang="typescript",
            topic="Формы",
            requirements=["FormArray removeAt", "addSkill push", "@for controls"],
        ),
        live(
            "FormControl updateOn blur",
            "Создайте UsernameComponent: FormControl с updateOn: 'blur'. "
            "Показывайте control.dirty и control.valid в шаблоне.",
            """import { Component } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-username',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <input [formControl]="username" />
    <p>Dirty: {{ username.dirty }} Valid: {{ username.valid }}</p>
  `,
})
export class UsernameComponent {
  username = new FormControl('', {
    nonNullable: true,
    validators: Validators.required,
    updateOn: 'blur',
  });
}""",
            lang="typescript",
            topic="Формы",
            requirements=["updateOn: 'blur'", "Validators.required", "dirty/valid в шаблоне"],
        ),
        live(
            "patchValue vs setValue",
            "Создайте ProfileFormComponent: FormGroup name/email. "
            "loadPartial() вызывает patchValue({ name: 'Ada' }), loadFull() — setValue оба поля.",
            """import { Component } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-profile-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `<form [formGroup]="form"><input formControlName="name" /><input formControlName="email" /></form>`,
})
export class ProfileFormComponent {
  form = this.fb.nonNullable.group({
    name: ['', Validators.required],
    email: ['', Validators.required],
  });

  constructor(private fb: FormBuilder) {}

  loadPartial() {
    this.form.patchValue({ name: 'Ada' });
  }

  loadFull() {
    this.form.setValue({ name: 'Ada', email: 'ada@example.com' });
  }
}""",
            lang="typescript",
            topic="Формы",
            requirements=["patchValue частично", "setValue полностью", "nonNullable group"],
        ),
        live(
            "valueChanges с startWith",
            "Создайте FilterComponent: filter FormControl, filtered$ = valueChanges.pipe(startWith(''), map). "
            "items signal, computed filtered по filter value.",
            """import { Component, computed, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { toSignal } from '@angular/core/rxjs-interop';
import { map, startWith } from 'rxjs';

@Component({
  selector: 'app-filter',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <input [formControl]="filter" />
    @for (item of filtered(); track item) { <span>{{ item }}</span> }
  `,
})
export class FilterComponent {
  items = signal(['apple', 'banana', 'apricot']);
  filter = new FormControl('', { nonNullable: true });
  private filterValue = toSignal(
    this.filter.valueChanges.pipe(startWith('')),
    { initialValue: '' }
  );
  filtered = computed(() => {
    const q = this.filterValue().toLowerCase();
    return this.items().filter(i => i.toLowerCase().includes(q));
  });
}""",
            lang="typescript",
            topic="Формы",
            requirements=["startWith('')", "toSignal + computed", "FormControl filter"],
        ),
        live(
            "Dynamic form from config",
            "Создайте DynamicFormComponent: config = [{ key: 'name', label: 'Name' }, { key: 'email', label: 'Email' }]. "
            "FormGroup строится в constructor из config keys.",
            """import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';

interface FieldConfig {
  key: string;
  label: string;
}

@Component({
  selector: 'app-dynamic-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form">
      @for (field of config; track field.key) {
        <label>{{ field.label }}<input [formControlName]="field.key" /></label>
      }
    </form>
  `,
})
export class DynamicFormComponent {
  config: FieldConfig[] = [
    { key: 'name', label: 'Name' },
    { key: 'email', label: 'Email' },
  ];
  form: FormGroup;

  constructor(private fb: FormBuilder) {
    this.form = this.fb.group(
      Object.fromEntries(this.config.map(f => [f.key, ['']]))
    );
  }
}""",
            lang="typescript",
            topic="Формы",
            requirements=["Config-driven fields", "FormGroup from keys", "@for по config"],
        ),
        live(
            "disable entire FormGroup",
            "Создайте LockedFormComponent: form.disable() в ngOnInit если readonly input true. "
            "input readonly = input(false).",
            """import { Component, effect, inject, input } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';

@Component({
  selector: 'app-locked-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `<form [formGroup]="form"><input formControlName="title" /></form>`,
})
export class LockedFormComponent {
  readonlyMode = input(false);
  form = inject(FormBuilder).nonNullable.group({ title: [''] });

  constructor() {
    effect(() => {
      if (this.readonlyMode()) this.form.disable();
      else this.form.enable();
    });
  }
}""",
            lang="typescript",
            topic="Формы",
            requirements=["form.disable()/enable()", "effect на input", "ReactiveFormsModule"],
        ),
        live(
            "statusChanges подписка",
            "Создайте FormStatusComponent: status = signal(''). "
            "В constructor подпишитесь на form.statusChanges и обновляйте status.",
            """import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-form-status',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `<p>Status: {{ status() }}</p><input formControlName="name" [formGroup]="form" />`,
})
export class FormStatusComponent {
  private fb = inject(FormBuilder);
  form = this.fb.nonNullable.group({ name: [''] });
  status = signal(this.form.status);

  constructor() {
    this.form.statusChanges.pipe(takeUntilDestroyed()).subscribe(s => this.status.set(s));
  }
}""",
            lang="typescript",
            topic="Формы",
            requirements=["statusChanges", "takeUntilDestroyed", "signal status"],
        ),
        live(
            "ngModel standalone",
            "Создайте NicknameComponent с [(ngModel)] nickname и параграфом preview. "
            "Импортируйте FormsModule, standalone.",
            """import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-nickname',
  standalone: true,
  imports: [FormsModule],
  template: `
    <input [(ngModel)]="nickname" placeholder="Nickname" />
    <p>Preview: {{ nickname }}</p>
  `,
})
export class NicknameComponent {
  nickname = '';
}""",
            lang="typescript",
            topic="Формы",
            requirements=["FormsModule", "[(ngModel)]", "Preview в шаблоне"],
        ),
        live(
            "FormRecord для динамических ключей",
            "Создайте ScoresComponent: FormRecord<FormControl<number>>. "
            "addScore(name) addControl, template keyvalue pipe или Object.keys.",
            """import { Component } from '@angular/core';
import { FormControl, FormRecord, ReactiveFormsModule } from '@angular/forms';
import { KeyValuePipe } from '@angular/common';

@Component({
  selector: 'app-scores',
  standalone: true,
  imports: [ReactiveFormsModule, KeyValuePipe],
  template: `
    <div [formGroup]="scores">
      @for (entry of scores.controls | keyvalue; track entry.key) {
        <input [formControlName]="entry.key" />
      }
    </div>
    <button type="button" (click)="addScore('math')">Add math</button>
  `,
})
export class ScoresComponent {
  scores = new FormRecord<FormControl<number>>({});

  addScore(name: string) {
    this.scores.addControl(name, new FormControl(0, { nonNullable: true }));
  }
}""",
            lang="typescript",
            topic="Формы",
            requirements=["FormRecord", "addControl", "keyvalue pipe"],
        ),
        live(
            "Signal forms stub (Angular 19+)",
            "Создайте SignalFormComponent с form = formGroup({ name: formControl('') }) из @angular/forms/signals. "
            "Шаблон [formField]=\"form.name\" (концептуальный stub).",
            """import { Component } from '@angular/core';
// Angular 19+ signal forms API (stub)
import { formControl, formGroup } from '@angular/forms/signals';

@Component({
  selector: 'app-signal-form',
  standalone: true,
  template: `
    <input [formField]="form.name" />
    <p>{{ form.name().value() }}</p>
  `,
})
export class SignalFormComponent {
  form = formGroup({
    name: formControl(''),
  });
}""",
            lang="typescript",
            topic="Формы",
            requirements=["formGroup/formControl signals API", "formField binding", "Angular 19+ stub"],
        ),
        live(
            "Custom validator forbiddenValue",
            "Создайте forbiddenValue(val: string): ValidatorFn и примените к FormControl в BanWordComponent. "
            "Покажите @if (word.hasError('forbidden')) в шаблоне.",
            """import { Component } from '@angular/core';
import { AbstractControl, FormControl, ReactiveFormsModule, ValidationErrors, ValidatorFn, Validators } from '@angular/forms';

export function forbiddenValue(val: string): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null =>
    control.value === val ? { forbidden: { value: control.value } } : null;
}

@Component({
  selector: 'app-ban-word',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <input [formControl]="word" />
    @if (word.hasError('forbidden')) { <p>Word banned</p> }
  `,
})
export class BanWordComponent {
  word = new FormControl('', {
    nonNullable: true,
    validators: [Validators.required, forbiddenValue('admin')],
  });
}""",
            lang="typescript",
            topic="Формы",
            requirements=["ValidatorFn factory", "hasError в шаблоне", "forbidden error key"],
        ),
        live(
            "FormGroup getRawValue с disabled",
            "Создайте CheckoutComponent: form с disabled coupon field. "
            "submit() логирует getRawValue() (включая disabled).",
            """import { Component } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';

@Component({
  selector: 'app-checkout',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()">
      <input formControlName="total" />
      <input formControlName="coupon" />
      <button type="submit">Pay</button>
    </form>
  `,
})
export class CheckoutComponent {
  form = this.fb.nonNullable.group({
    total: [100],
    coupon: [{ value: 'SAVE10', disabled: true }],
  });

  constructor(private fb: FormBuilder) {}

  submit() {
    console.log(this.form.getRawValue());
  }
}""",
            lang="typescript",
            topic="Формы",
            requirements=["disabled control", "getRawValue()", "nonNullable group"],
        ),

        # ── Роутинг (46–60) ──
        live(
            "CanMatch functional guard",
            "Создайте adminMatchGuard: CanMatchFn — inject AuthService, return role === 'admin'. "
            "Используйте в route canMatch: [adminMatchGuard].",
            """import { inject } from '@angular/core';
import { CanMatchFn } from '@angular/router';
import { AuthService } from './auth.service';

export const adminMatchGuard: CanMatchFn = () => {
  return inject(AuthService).role() === 'admin';
};""",
            lang="typescript",
            topic="Роутинг",
            requirements=["CanMatchFn", "inject(AuthService)", "role check"],
        ),
        live(
            "CanActivateChild guard",
            "Создайте authChildGuard: CanActivateChildFn — проверяет isLoggedIn для всех child routes.",
            """import { inject } from '@angular/core';
import { CanActivateChildFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authChildGuard: CanActivateChildFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.isLoggedIn() ? true : router.parseUrl('/login');
};""",
            lang="typescript",
            topic="Роутинг",
            requirements=["CanActivateChildFn", "parseUrl redirect", "inject pattern"],
        ),
        live(
            "Resolver с forkJoin",
            "Создайте dashboardResolver: ResolveFn — forkJoin user + stats, return { user, stats }.",
            """import { inject } from '@angular/core';
import { ResolveFn } from '@angular/router';
import { forkJoin, map } from 'rxjs';
import { UserApi } from './user-api';
import { StatsApi } from './stats-api';

export const dashboardResolver: ResolveFn<{ user: unknown; stats: unknown }> = () => {
  const users = inject(UserApi);
  const stats = inject(StatsApi);
  return forkJoin({ user: users.me(), stats: stats.summary() });
};""",
            lang="typescript",
            topic="Роутинг",
            requirements=["ResolveFn", "forkJoin", "inject APIs"],
        ),
        live(
            "Lazy loadChildren routes",
            "Создайте routes с path 'reports' loadChildren: () => import('./reports.routes').then(m => m.REPORT_ROUTES).",
            """import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'reports',
    loadChildren: () => import('./reports/reports.routes').then(m => m.REPORT_ROUTES),
  },
];""",
            lang="typescript",
            topic="Роутинг",
            requirements=["loadChildren", "Dynamic import routes", "path reports"],
        ),
        live(
            "Wildcard redirect 404",
            "Создайте routes: path '**' redirectTo 'not-found', pathMatch 'full'. "
            "И route not-found с loadComponent NotFoundPage.",
            """import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'not-found',
    loadComponent: () => import('./not-found.page').then(m => m.NotFoundPage),
  },
  { path: '**', redirectTo: 'not-found', pathMatch: 'full' },
];""",
            lang="typescript",
            topic="Роутинг",
            requirements=["Wildcard **", "redirectTo not-found", "loadComponent"],
        ),
        live(
            "withComponentInputBinding",
            "Создайте routes с :id param и UserDetailPage. "
            "provideRouter(routes, withComponentInputBinding()) в main.ts.",
            """import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { AppComponent } from './app.component';
import { routes } from './app.routes';

bootstrapApplication(AppComponent, {
  providers: [provideRouter(routes, withComponentInputBinding())],
});

// UserDetailPage: id = input.required<string>()""",
            lang="typescript",
            topic="Роутинг",
            requirements=["withComponentInputBinding", "Route param → input", "bootstrapApplication"],
        ),
        live(
            "queryParams в компоненте",
            "Создайте SearchPageComponent: inject ActivatedRoute, queryParams pipe map q => q['q']. "
            "query = toSignal(..., { initialValue: '' }).",
            """import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';

@Component({
  selector: 'app-search-page',
  standalone: true,
  template: `<p>Query: {{ query() }}</p>`,
})
export class SearchPageComponent {
  private route = inject(ActivatedRoute);
  query = toSignal(
    this.route.queryParams.pipe(map(p => p['q'] ?? '')),
    { initialValue: '' }
  );
}""",
            lang="typescript",
            topic="Роутинг",
            requirements=["ActivatedRoute queryParams", "toSignal", "map q param"],
        ),
        live(
            "Router navigate с fragment",
            "Создайте DocsComponent: scrollTo(section) вызывает router.navigate([], { fragment: section }). "
            "inject Router.",
            """import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-docs',
  standalone: true,
  template: `
    <button type="button" (click)="scrollTo('intro')">Intro</button>
    <button type="button" (click)="scrollTo('api')">API</button>
  `,
})
export class DocsComponent {
  private router = inject(Router);

  scrollTo(section: string) {
    this.router.navigate([], { fragment: section });
  }
}""",
            lang="typescript",
            topic="Роутинг",
            requirements=["router.navigate fragment", "inject Router", "empty path array"],
        ),
        live(
            "Named router outlet",
            "Создайте routes с component ShellComponent, children outlet 'sidebar' loadComponent SidebarComponent.",
            """import { Routes } from '@angular/router';
import { ShellComponent } from './shell.component';

export const routes: Routes = [
  {
    path: 'app',
    component: ShellComponent,
    children: [
      { path: 'sidebar', outlet: 'sidebar', loadComponent: () => import('./sidebar').then(m => m.SidebarComponent) },
    ],
  },
];""",
            lang="typescript",
            topic="Роутинг",
            requirements=["Named outlet sidebar", "children routes", "loadComponent"],
        ),
        live(
            "Route title resolver function",
            "Создайте route с title: () => inject(TitleService).getPageTitle('products'). "
            "TitleService возвращает string.",
            """import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { TitleService } from './title.service';
import { ProductsPage } from './products.page';

export const routes: Routes = [
  {
    path: 'products',
    component: ProductsPage,
    title: () => inject(TitleService).getPageTitle('products'),
  },
];""",
            lang="typescript",
            topic="Роутинг",
            requirements=["Dynamic title function", "inject in route config", "TitleService"],
        ),
        live(
            "runGuardsAndResolvers always",
            "Создайте route с runGuardsAndResolvers: 'always' и resolve: itemResolver для :id.",
            """import { Routes } from '@angular/router';
import { itemResolver } from './item.resolver';
import { ItemPage } from './item.page';

export const routes: Routes = [
  {
    path: 'items/:id',
    component: ItemPage,
    resolve: { item: itemResolver },
    runGuardsAndResolvers: 'always',
  },
];""",
            lang="typescript",
            topic="Роутинг",
            requirements=["runGuardsAndResolvers: 'always'", "resolve item", "param :id"],
        ),
        live(
            "RouterLink с queryParams",
            "Создайте FilterLinkComponent: a routerLink='/products' [queryParams]=\"{ sort: 'price' }\".",
            """import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-filter-link',
  standalone: true,
  imports: [RouterLink],
  template: `<a routerLink="/products" [queryParams]="{ sort: 'price' }">Sort by price</a>`,
})
export class FilterLinkComponent {}""",
            lang="typescript",
            topic="Роутинг",
            requirements=["RouterLink", "queryParams binding", "Standalone"],
        ),
        live(
            "CanDeactivate с Observable",
            "Создайте pendingChangesGuard: CanDeactivateFn возвращает dialog.confirm() как Observable<boolean>.",
            """import { inject } from '@angular/core';
import { CanDeactivateFn } from '@angular/router';
import { DialogService } from './dialog.service';

export interface ConfirmLeave {
  hasPendingChanges(): boolean;
}

export const pendingChangesGuard: CanDeactivateFn<ConfirmLeave> = component => {
  if (!component.hasPendingChanges()) return true;
  return inject(DialogService).confirm('Leave without saving?');
};""",
            lang="typescript",
            topic="Роутинг",
            requirements=["CanDeactivateFn", "Observable confirm", "hasPendingChanges interface"],
        ),
        live(
            "Preloading strategy stub",
            "Создайте CustomPreloadStrategy implements PreloadingStrategy: preload route если data.preload === true.",
            """import { Injectable } from '@angular/core';
import { PreloadingStrategy, Route } from '@angular/router';
import { Observable, of } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class CustomPreloadStrategy implements PreloadingStrategy {
  preload(route: Route, load: () => Observable<unknown>): Observable<unknown> {
    return route.data?.['preload'] ? load() : of(null);
  }
}""",
            lang="typescript",
            topic="Роутинг",
            requirements=["PreloadingStrategy", "route.data preload flag", "providedIn root"],
        ),
        live(
            "Router events NavigationEnd",
            "Создайте AnalyticsComponent: inject Router, filter events NavigationEnd, "
            "toSignal для url после NavigationEnd.",
            """import { Component, inject } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { filter, map } from 'rxjs';

@Component({
  selector: 'app-analytics',
  standalone: true,
  template: `<p>Current: {{ url() }}</p>`,
})
export class AnalyticsComponent {
  private router = inject(Router);
  url = toSignal(
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      map(e => e.urlAfterRedirects)
    ),
    { initialValue: '/' }
  );
}""",
            lang="typescript",
            topic="Роутинг",
            requirements=["NavigationEnd filter", "toSignal url", "urlAfterRedirects"],
        ),

        # ── HTTP и RxJS (61–75) ──
        live(
            "combineLatest в компоненте",
            "Создайте DashboardComponent: combineLatest([user$, settings$]) pipe map(([user, settings]) => ({ user, settings })). "
            "Отобразите через async pipe или toSignal.",
            """import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { combineLatest, map } from 'rxjs';
import { UserApi } from './user-api';
import { SettingsApi } from './settings-api';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  template: `@if (vm(); as d) { <p>{{ d.user.name }} / {{ d.settings.theme }}</p> }`,
})
export class DashboardComponent {
  private users = inject(UserApi);
  private settings = inject(SettingsApi);
  vm = toSignal(
    combineLatest([this.users.me(), this.settings.get()]).pipe(
      map(([user, settings]) => ({ user, settings }))
    ),
    { initialValue: null }
  );
}""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["combineLatest", "map tuple", "toSignal vm"],
        ),
        live(
            "switchMap live search",
            "Создайте ProductSearchComponent: q FormControl, results$ = valueChanges pipe debounceTime, distinctUntilChanged, switchMap(search). "
            "Template @for по results$ | async.",
            """import { Component, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { AsyncPipe } from '@angular/common';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import { ProductApi } from './product-api';

@Component({
  selector: 'app-product-search',
  standalone: true,
  imports: [ReactiveFormsModule, AsyncPipe],
  template: `
    <input [formControl]="q" />
    @for (p of results$ | async; track p.id) { <div>{{ p.name }}</div> }
  `,
})
export class ProductSearchComponent {
  private api = inject(ProductApi);
  q = new FormControl('', { nonNullable: true });
  results$ = this.q.valueChanges.pipe(
    debounceTime(300),
    distinctUntilChanged(),
    switchMap(term => this.api.search(term))
  );
}""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["switchMap", "debounceTime + distinctUntilChanged", "AsyncPipe"],
        ),
        live(
            "forkJoin параллельные запросы",
            "Создайте OrderSummaryService load(orderId): forkJoin items + customer, map в OrderSummary.",
            """import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { forkJoin, map } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class OrderSummaryService {
  private http = inject(HttpClient);

  load(orderId: string) {
    return forkJoin({
      items: this.http.get<Item[]>(`/api/orders/${orderId}/items`),
      customer: this.http.get<Customer>(`/api/orders/${orderId}/customer`),
    }).pipe(map(({ items, customer }) => ({ orderId, items, customer })));
  }
}

interface Item { id: string; name: string }
interface Customer { id: string; name: string }""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["forkJoin", "HttpClient GET", "map to summary"],
        ),
        live(
            "mergeMap upload files",
            "Создайте UploadService uploadAll(files: File[]): from(files) pipe mergeMap(f => upload(f)).",
            """import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { from, mergeMap } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class UploadService {
  private http = inject(HttpClient);

  uploadAll(files: File[]) {
    return from(files).pipe(
      mergeMap(file => this.http.post<{ id: string }>('/api/upload', file))
    );
  }
}""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["from(files)", "mergeMap", "HttpClient POST"],
        ),
        live(
            "exhaustMap submit button",
            "Создайте SubmitComponent: submit$ Subject, results$ = submit$.pipe(exhaustMap(() => api.save())). "
            "Кнопка (click)=\"submit$.next()\".",
            """import { Component, inject } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { Subject, exhaustMap } from 'rxjs';
import { SaveApi } from './save-api';

@Component({
  selector: 'app-submit',
  standalone: true,
  imports: [AsyncPipe],
  template: `
    <button type="button" (click)="submit$.next()">Save</button>
    @if (result$ | async; as r) { <p>Saved {{ r.id }}</p> }
  `,
})
export class SubmitComponent {
  private api = inject(SaveApi);
  submit$ = new Subject<void>();
  result$ = this.submit$.pipe(exhaustMap(() => this.api.save()));
}""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["Subject trigger", "exhaustMap", "AsyncPipe result"],
        ),
        live(
            "catchError с fallback",
            "Создайте SafeLoadComponent: data$ = api.load().pipe(catchError(() => of([]))). "
            "toSignal с initialValue [].",
            """import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { catchError, of } from 'rxjs';
import { DataApi } from './data-api';

@Component({
  selector: 'app-safe-load',
  standalone: true,
  template: `@for (item of data(); track item.id) { <p>{{ item.name }}</p> }`,
})
export class SafeLoadComponent {
  private api = inject(DataApi);
  data = toSignal(
    this.api.load().pipe(catchError(() => of([] as Item[]))),
    { initialValue: [] as Item[] }
  );
}

interface Item { id: number; name: string }""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["catchError fallback of([])", "toSignal", "Http load"],
        ),
        live(
            "retry operator HTTP",
            "Создайте ResilientApi get(): http.get pipe retry({ count: 3, delay: 1000 }).",
            """import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { retry } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ResilientApi {
  private http = inject(HttpClient);

  get<T>(url: string) {
    return this.http.get<T>(url).pipe(retry({ count: 3, delay: 1000 }));
  }
}""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["retry count/delay", "HttpClient get", "Generic T"],
        ),
        live(
            "shareReplay в сервисе",
            "Создайте ConfigService: config$ = http.get('/api/config').pipe(shareReplay(1)). "
            "Поле private, метод getConfig() возвращает config$.",
            """import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { shareReplay } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ConfigService {
  private http = inject(HttpClient);
  private config$ = this.http.get<AppConfig>('/api/config').pipe(shareReplay(1));

  getConfig() {
    return this.config$;
  }
}

interface AppConfig { theme: string; locale: string }""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["shareReplay(1)", "Cached config$", "providedIn root"],
        ),
        live(
            "BehaviorSubject event bus",
            "Создайте EventBus<T>: private subject = new BehaviorSubject<T | null>(null), "
            "emit(value), on$() возвращает asObservable().",
            """import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class EventBus<T> {
  private subject = new BehaviorSubject<T | null>(null);

  emit(value: T) {
    this.subject.next(value);
  }

  on$() {
    return this.subject.asObservable();
  }
}""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["BehaviorSubject", "emit/on$", "Generic EventBus"],
        ),
        live(
            "HttpClient с HttpParams",
            "Создайте ArticleApi list(page, q): HttpParams set page и q, GET /api/articles.",
            """import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class ArticleApi {
  private http = inject(HttpClient);

  list(page: number, q: string) {
    const params = new HttpParams().set('page', page).set('q', q);
    return this.http.get<Article[]>('/api/articles', { params });
  }
}

interface Article { id: number; title: string }""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["HttpParams", "GET with params", "list(page, q)"],
        ),
        live(
            "HttpClient observe response",
            "Создайте DownloadApi fetchMeta(url): observe 'response', map res => ({ body: res.body, etag: res.headers.get('ETag') }).",
            """import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class DownloadApi {
  private http = inject(HttpClient);

  fetchMeta(url: string) {
    return this.http.get(url, { observe: 'response' }).pipe(
      map(res => ({
        body: res.body,
        etag: res.headers.get('ETag'),
      }))
    );
  }
}""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["observe: 'response'", "headers.get ETag", "map response"],
        ),
        live(
            "Timeout operator",
            "Создайте QuickApi load(): http.get pipe timeout(5000), catchError throw user-friendly error.",
            """import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, timeout, throwError } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class QuickApi {
  private http = inject(HttpClient);

  load() {
    return this.http.get<Data[]>('/api/data').pipe(
      timeout(5000),
      catchError(err => throwError(() => new Error('Request timed out')))
    );
  }
}

interface Data { id: number }""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["timeout(5000)", "catchError throwError", "HttpClient GET"],
        ),
        live(
            "map filter chain",
            "Создайте ActiveUsersComponent: users$ = api.getUsers().pipe(map(list => list.filter(u => u.active))).",
            """import { Component, inject } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { map } from 'rxjs';
import { UserApi, User } from './user-api';

@Component({
  selector: 'app-active-users',
  standalone: true,
  imports: [AsyncPipe],
  template: `@for (u of active$ | async; track u.id) { <p>{{ u.name }}</p> }`,
})
export class ActiveUsersComponent {
  private api = inject(UserApi);
  active$ = this.api.getUsers().pipe(map((list: User[]) => list.filter(u => u.active)));
}""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["map + filter", "AsyncPipe", "UserApi"],
        ),
        live(
            "HttpInterceptorFn logging",
            "Создайте loggingInterceptor: console.log method url, return next(req).",
            """import { HttpInterceptorFn } from '@angular/common/http';

export const loggingInterceptor: HttpInterceptorFn = (req, next) => {
  console.log(`${req.method} ${req.url}`);
  return next(req);
};""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["HttpInterceptorFn", "Log method/url", "next(req)"],
        ),
        live(
            "provideHttpClient withInterceptors",
            "Создайте app.config.ts: provideHttpClient(withInterceptors([loggingInterceptor, authInterceptor])).",
            """import { ApplicationConfig } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { loggingInterceptor } from './logging.interceptor';
import { authInterceptor } from './auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(withInterceptors([loggingInterceptor, authInterceptor])),
  ],
};""",
            lang="typescript",
            topic="HTTP и RxJS",
            requirements=["withInterceptors", "Multiple interceptors", "ApplicationConfig"],
        ),

        # ── Сигналы (76–90) ──
        live(
            "linkedSignal базовый",
            "Создайте BreadcrumbComponent: items = input<string[]>([]), "
            "trail = linkedSignal(() => this.items().join(' › ')). Шаблон {{ trail() }}.",
            """import { Component, input, linkedSignal } from '@angular/core';

@Component({
  selector: 'app-breadcrumb',
  standalone: true,
  template: `<nav>{{ trail() }}</nav>`,
})
export class BreadcrumbComponent {
  items = input<string[]>([]);
  trail = linkedSignal(() => this.items().join(' › '));
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["linkedSignal", "input items", "join trail"],
        ),
        live(
            "linkedSignal с previous value",
            "Создайте AccumulatorComponent: value input, total = linkedSignal({ source: value, computation: (v, prev) => (prev?.value ?? 0) + v }). "
            "Концептуальный stub linkedSignal API.",
            """import { Component, input, linkedSignal } from '@angular/core';

@Component({
  selector: 'app-accumulator',
  standalone: true,
  template: `<p>Total: {{ total() }}</p>`,
})
export class AccumulatorComponent {
  value = input(0);
  total = linkedSignal({
    source: this.value,
    computation: (v, prev) => (prev?.value ?? 0) + v,
  });
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["linkedSignal source/computation", "Previous value", "input number"],
        ),
        live(
            "computed derived state",
            "Создайте CartComponent: items = signal<CartItem[]>([]), "
            "total = computed(() => items().reduce((s, i) => s + i.price * i.qty, 0)).",
            """import { Component, computed, signal } from '@angular/core';

interface CartItem {
  id: number;
  price: number;
  qty: number;
}

@Component({
  selector: 'app-cart',
  standalone: true,
  template: `<p>Total: {{ total() }}</p>`,
})
export class CartComponent {
  items = signal<CartItem[]>([{ id: 1, price: 10, qty: 2 }]);
  total = computed(() => this.items().reduce((s, i) => s + i.price * i.qty, 0));
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["computed reduce", "signal CartItem[]", "total price*qty"],
        ),
        live(
            "effect с allowSignalWrites",
            "Создайте SyncComponent: source = signal(0), mirror = signal(0). "
            "effect(() => mirror.set(source()), { allowSignalWrites: true }).",
            """import { Component, effect, signal } from '@angular/core';

@Component({
  selector: 'app-sync',
  standalone: true,
  template: `
    <p>Source: {{ source() }} Mirror: {{ mirror() }}</p>
    <button (click)="source.update(v => v + 1)">+</button>
  `,
})
export class SyncComponent {
  source = signal(0);
  mirror = signal(0);

  constructor() {
    effect(() => this.mirror.set(this.source()), { allowSignalWrites: true });
  }
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["effect allowSignalWrites", "mirror.set", "source signal"],
        ),
        live(
            "untracked в effect",
            "Создайте LoggerComponent: count signal, effect логирует count но читает untracked(() => settings.get()).",
            """import { Component, effect, inject, signal, untracked } from '@angular/core';
import { SettingsService } from './settings.service';

@Component({
  selector: 'app-logger',
  standalone: true,
  template: `<button (click)="count.update(v => v + 1)">{{ count() }}</button>`,
})
export class LoggerComponent {
  private settings = inject(SettingsService);
  count = signal(0);

  constructor() {
    effect(() => {
      const n = this.count();
      const theme = untracked(() => this.settings.theme());
      console.log(n, theme);
    });
  }
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["untracked()", "effect logging", "SettingsService inject"],
        ),
        live(
            "toObservable из signal",
            "Создайте SignalBridgeComponent: term = signal(''), term$ = toObservable(term). "
            "Подписка pipe debounceTime в constructor.",
            """import { Component, signal } from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import { debounceTime } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-signal-bridge',
  standalone: true,
  template: `<input [value]="term()" (input)="term.set($any($event.target).value)" />`,
})
export class SignalBridgeComponent {
  term = signal('');
  term$ = toObservable(this.term);

  constructor() {
    this.term$.pipe(debounceTime(300), takeUntilDestroyed()).subscribe(v => console.log(v));
  }
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["toObservable(signal)", "debounceTime", "takeUntilDestroyed"],
        ),
        live(
            "toSignal из Observable",
            "Создайте ClockComponent: now = toSignal(interval(1000).pipe(map(() => new Date())), { initialValue: new Date() }).",
            """import { Component } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { interval, map } from 'rxjs';

@Component({
  selector: 'app-clock',
  standalone: true,
  template: `<time>{{ now() | date: 'mediumTime' }}</time>`,
})
export class ClockComponent {
  now = toSignal(interval(1000).pipe(map(() => new Date())), { initialValue: new Date() });
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["toSignal interval", "initialValue Date", "DatePipe in template"],
        ),
        live(
            "viewChild signal required",
            "Создайте FocusHostComponent: input = viewChild.required<ElementRef>('input'). "
            "ngAfterViewInit — input().nativeElement.focus().",
            """import { AfterViewInit, Component, ElementRef, viewChild } from '@angular/core';

@Component({
  selector: 'app-focus-host',
  standalone: true,
  template: `<input #input type="text" />`,
})
export class FocusHostComponent implements AfterViewInit {
  input = viewChild.required<ElementRef<HTMLInputElement>>('input');

  ngAfterViewInit() {
    this.input().nativeElement.focus();
  }
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["viewChild.required", "ElementRef focus", "AfterViewInit"],
        ),
        live(
            "contentChild signal",
            "Создайте TabsComponent: activeTab = contentChild(TabComponent). "
            "Stub TabComponent selector app-tab.",
            """import { Component, contentChild } from '@angular/core';
import { TabComponent } from './tab.component';

@Component({
  selector: 'app-tabs',
  standalone: true,
  imports: [TabComponent],
  template: `<ng-content></ng-content>`,
})
export class TabsComponent {
  activeTab = contentChild(TabComponent);
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["contentChild signal", "TabComponent", "ng-content"],
        ),
        live(
            "resource API stub",
            "Создайте UserResourceComponent: user = resource({ loader: () => fetch('/api/me').then(r => r.json()) }). "
            "Шаблон @if (user.hasValue()) { user.value().name }.",
            """import { Component, resource } from '@angular/core';

@Component({
  selector: 'app-user-resource',
  standalone: true,
  template: `
    @if (user.hasValue()) {
      <p>{{ user.value().name }}</p>
    } @else if (user.isLoading()) {
      <p>Loading…</p>
    }
  `,
})
export class UserResourceComponent {
  user = resource({
    loader: () => fetch('/api/me').then(r => r.json() as Promise<{ name: string }>),
  });
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["resource() loader", "hasValue/isLoading", "Angular 19+ API"],
        ),
        live(
            "rxResource stub",
            "Создайте ProductsResource: products = rxResource({ request: () => ({}), loader: () => http.get('/api/products') }). "
            "Концептуальный Angular 19 stub.",
            """import { Component, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { rxResource } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-products-resource',
  standalone: true,
  template: `@for (p of products.value() ?? []; track p.id) { <p>{{ p.name }}</p> }`,
})
export class ProductsResourceComponent {
  private http = inject(HttpClient);
  products = rxResource({
    request: () => ({}),
    loader: () => this.http.get<Product[]>('/api/products'),
  });
}

interface Product { id: number; name: string }""",
            lang="typescript",
            topic="Сигналы",
            requirements=["rxResource", "HttpClient loader", "value() in template"],
        ),
        live(
            "signal writable model parent",
            "Создайте EditorHostComponent с [(value)]=\"text\" на ChildEditorComponent. "
            "Child использует model<string>('').",
            """import { Component, signal } from '@angular/core';
import { ChildEditorComponent } from './child-editor.component';

@Component({
  selector: 'app-editor-host',
  standalone: true,
  imports: [ChildEditorComponent],
  template: `
    <app-child-editor [(value)]="text" />
    <p>Host: {{ text() }}</p>
  `,
})
export class EditorHostComponent {
  text = signal('hello');
}

// ChildEditorComponent: value = model('');""",
            lang="typescript",
            topic="Сигналы",
            requirements=["model() two-way", "Host signal", "[(value)] binding"],
        ),
        live(
            "signal update vs set",
            "Создайте CounterComponent демонстрирующий count.set(0) и count.update(v => v + 1). "
            "Две кнопки Reset и Increment.",
            """import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-counter',
  standalone: true,
  template: `
    <p>{{ count() }}</p>
    <button type="button" (click)="count.set(0)">Reset</button>
    <button type="button" (click)="count.update(v => v + 1)">+</button>
  `,
})
export class CounterComponent {
  count = signal(0);
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["set vs update", "signal counter", "Две кнопки"],
        ),
        live(
            "input.required transform",
            "Создайте PriceComponent: amount = input.required({ transform: (v: string | number) => Number(v) }). "
            "computed formatted = computed(() => amount().toFixed(2)).",
            """import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-price',
  standalone: true,
  template: `<span>{{ formatted() }}</span>`,
})
export class PriceComponent {
  amount = input.required({ transform: (v: string | number) => Number(v) });
  formatted = computed(() => this.amount().toFixed(2));
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["input.required transform", "computed toFixed", "Number coercion"],
        ),
        live(
            "NgOptimizedImage в signal host",
            "Создайте HeroImageComponent: src = input('/hero.webp'), "
            "шаблон img ngSrc=\"src()\" width height priority.",
            """import { Component, input } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';

@Component({
  selector: 'app-hero-image',
  standalone: true,
  imports: [NgOptimizedImage],
  template: `
    <img [ngSrc]="src()" width="1200" height="600" priority alt="Hero" />
  `,
})
export class HeroImageComponent {
  src = input('/hero.webp');
}""",
            lang="typescript",
            topic="Сигналы",
            requirements=["NgOptimizedImage", "input src signal", "priority flag"],
        ),

        # ── DI и провайдеры (91–104) ──
        live(
            "useClass provider",
            "Создайте Logger interface, ConsoleLogger implements, providers: [{ provide: Logger, useClass: ConsoleLogger }].",
            """import { Injectable, InjectionToken, inject } from '@angular/core';

export abstract class Logger {
  abstract log(msg: string): void;
}

@Injectable()
export class ConsoleLogger implements Logger {
  log(msg: string) {
    console.log(msg);
  }
}

export const LOGGER = new InjectionToken<Logger>('Logger');

// providers: [{ provide: LOGGER, useClass: ConsoleLogger }]""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["InjectionToken", "useClass", "ConsoleLogger"],
        ),
        live(
            "useFactory provider",
            "Создайте API_URL token, factory (config: AppConfig) => config.apiBase, deps: [AppConfig].",
            """import { InjectionToken } from '@angular/core';
import { AppConfig } from './app-config';

export const API_URL = new InjectionToken<string>('API_URL');

export const apiUrlProvider = {
  provide: API_URL,
  useFactory: (config: AppConfig) => config.apiBase,
  deps: [AppConfig],
};""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["useFactory", "deps: [AppConfig]", "InjectionToken API_URL"],
        ),
        live(
            "useExisting alias provider",
            "Создайте AliasedLogger: provide LOGGER useExisting ConsoleLogger — оба указывают на один instance.",
            """import { Injectable, InjectionToken } from '@angular/core';

export const LOGGER = new InjectionToken<Logger>('Logger');
export const LEGACY_LOGGER = new InjectionToken<Logger>('LegacyLogger');

@Injectable()
export class ConsoleLogger implements Logger {
  log(msg: string) { console.log(msg); }
}

export interface Logger { log(msg: string): void }

export const loggerProviders = [
  ConsoleLogger,
  { provide: LOGGER, useExisting: ConsoleLogger },
  { provide: LEGACY_LOGGER, useExisting: ConsoleLogger },
];""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["useExisting", "Same instance", "Two tokens"],
        ),
        live(
            "optional inject",
            "Создайте FeatureComponent: theme = inject(THEME, { optional: true }) ?? 'light'. "
            "THEME InjectionToken<string>.",
            """import { Component, InjectionToken, inject } from '@angular/core';

export const THEME = new InjectionToken<string>('THEME');

@Component({
  selector: 'app-feature',
  standalone: true,
  template: `<div [attr.data-theme]="theme">Feature</div>`,
})
export class FeatureComponent {
  theme = inject(THEME, { optional: true }) ?? 'light';
}""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["inject optional", "Nullish coalescing default", "InjectionToken"],
        ),
        live(
            "self skipSelf inject",
            "Создайте ParentComponent providers: [ValueService], ChildComponent inject(ValueService, { skipSelf: true, optional: true }).",
            """import { Component, Injectable, inject } from '@angular/core';

@Injectable()
export class ValueService {
  value = 'local';
}

@Component({
  selector: 'app-child',
  standalone: true,
  template: `<p>{{ parentValue ?? 'none' }}</p>`,
})
export class ChildComponent {
  parentValue = inject(ValueService, { skipSelf: true, optional: true })?.value;
}

@Component({
  selector: 'app-parent',
  standalone: true,
  imports: [ChildComponent],
  providers: [ValueService],
  template: `<app-child />`,
})
export class ParentComponent {}""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["skipSelf: true", "Component providers", "optional inject"],
        ),
        live(
            "multi provider TOKENS",
            "Создайте multi: true provide VALIDATORS useValue fn1 и fn2.",
            """import { InjectionToken } from '@angular/core';

export type ValidatorFn = (value: string) => string | null;

export const VALIDATORS = new InjectionToken<ValidatorFn[]>('VALIDATORS');

export const validatorProviders = [
  { provide: VALIDATORS, useValue: (v: string) => (v.length ? null : 'Required'), multi: true },
  { provide: VALIDATORS, useValue: (v: string) => (v.length >= 3 ? null : 'Too short'), multi: true },
];""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["multi: true", "InjectionToken array", "Two useValue"],
        ),
        live(
            "APP_INITIALIZER",
            "Создайте initConfig(): inject ConfigService).load() return Promise. "
            "provide: APP_INITIALIZER, useFactory: initConfig, multi: true.",
            """import { APP_INITIALIZER, inject } from '@angular/core';
import { ConfigService } from './config.service';

export function initConfig() {
  const config = inject(ConfigService);
  return () => config.load();
}

export const appInitProvider = {
  provide: APP_INITIALIZER,
  useFactory: initConfig,
  multi: true,
};""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["APP_INITIALIZER", "inject in factory", "multi: true"],
        ),
        live(
            "provideAnimations stub",
            "Создайте app.config.ts с provideAnimations() из @angular/platform-browser/animations.",
            """import { ApplicationConfig } from '@angular/core';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [provideRouter(routes), provideAnimations()],
};""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["provideAnimations()", "ApplicationConfig", "provideRouter"],
        ),
        live(
            "provideAppInitializer (Angular 19)",
            "Создайте provideAppInitializer(() => inject(TelemetryService).init()). "
            "Stub TelemetryService.",
            """import { inject, provideAppInitializer } from '@angular/core';
import { TelemetryService } from './telemetry.service';

export const telemetryInit = provideAppInitializer(() => {
  inject(TelemetryService).init();
});""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["provideAppInitializer", "inject TelemetryService", "init side effect"],
        ),
        live(
            "EnvironmentInjector runInInjectionContext",
            "Создайте runWithApi(): runInInjectionContext(envInjector, () => inject(ApiClient).ping()).",
            """import { EnvironmentInjector, inject, runInInjectionContext } from '@angular/core';
import { ApiClient } from './api-client';

export function runWithApi(envInjector: EnvironmentInjector) {
  return runInInjectionContext(envInjector, () => inject(ApiClient).ping());
}""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["runInInjectionContext", "EnvironmentInjector param", "inject ApiClient"],
        ),
        live(
            "PLATFORM_ID isPlatformBrowser",
            "Создайте StorageService: constructor inject PLATFORM_ID, isPlatformBrowser guard для localStorage.",
            """import { Injectable, PLATFORM_ID, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Injectable({ providedIn: 'root' })
export class StorageService {
  private platformId = inject(PLATFORM_ID);

  get(key: string): string | null {
    if (!isPlatformBrowser(this.platformId)) return null;
    return localStorage.getItem(key);
  }

  set(key: string, value: string) {
    if (isPlatformBrowser(this.platformId)) localStorage.setItem(key, value);
  }
}""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["PLATFORM_ID", "isPlatformBrowser", "localStorage guard"],
        ),
        live(
            "Component-level providers",
            "Создайте TreeComponent providers: [TreeStateService], дочерние узлы inject TreeStateService.",
            """import { Component, Injectable, inject } from '@angular/core';

@Injectable()
export class TreeStateService {
  expanded = new Set<string>();
  toggle(id: string) {
    this.expanded.has(id) ? this.expanded.delete(id) : this.expanded.add(id);
  }
}

@Component({
  selector: 'app-tree',
  standalone: true,
  providers: [TreeStateService],
  template: `<app-tree-node />`,
})
export class TreeComponent {
  state = inject(TreeStateService);
}""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["Component providers", "TreeStateService", "inject in component"],
        ),
        live(
            "forwardRef для circular DI",
            "Создайте ParentService inject(forwardRef(() => ChildService)), ChildService inject(ParentService).",
            """import { Injectable, forwardRef, inject } from '@angular/core';

@Injectable()
export class ChildService {
  parent = inject(forwardRef(() => ParentService));
}

@Injectable()
export class ParentService {
  child = inject(ChildService);
  ping() {
    return 'pong';
  }
}""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["forwardRef(() => ...)", "Circular DI", "Two services"],
        ),
        live(
            "i18n stub provideTransloco/LOCALE_ID",
            "Создайте app.config providers: { provide: LOCALE_ID, useValue: 'ru-RU' }. "
            "Компонент inject LOCALE_ID.",
            """import { Component, LOCALE_ID, inject } from '@angular/core';

@Component({
  selector: 'app-locale-info',
  standalone: true,
  template: `<p>Locale: {{ locale }}</p>`,
})
export class LocaleInfoComponent {
  locale = inject(LOCALE_ID);
}

// providers: [{ provide: LOCALE_ID, useValue: 'ru-RU' }]""",
            lang="typescript",
            topic="DI и провайдеры",
            requirements=["LOCALE_ID token", "useValue ru-RU", "inject in component"],
        ),

        # ── Pipes и CVA (105–118) ──
        live(
            "Pure pipe capitalize",
            "Создайте CapitalizePipe standalone: transform(value: string): string — первая буква uppercase.",
            """import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'capitalize', standalone: true })
export class CapitalizePipe implements PipeTransform {
  transform(value: string): string {
    if (!value) return '';
    return value.charAt(0).toUpperCase() + value.slice(1);
  }
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["standalone Pipe", "PipeTransform", "Capitalize first letter"],
        ),
        live(
            "Impure pipe timestamp",
            "Создайте NowPipe pure: false, transform() return new Date().toLocaleTimeString().",
            """import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'now', standalone: true, pure: false })
export class NowPipe implements PipeTransform {
  transform(): string {
    return new Date().toLocaleTimeString();
  }
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["pure: false", "Impure pipe", "toLocaleTimeString"],
        ),
        live(
            "DatePipe в шаблоне",
            "Создайте EventComponent: date = signal(new Date()), шаблон {{ date() | date:'fullDate':'':'ru-RU' }}.",
            """import { Component, signal } from '@angular/core';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-event',
  standalone: true,
  imports: [DatePipe],
  template: `<p>{{ date() | date: 'fullDate' : '' : 'ru-RU' }}</p>`,
})
export class EventComponent {
  date = signal(new Date());
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["DatePipe import", "fullDate format", "ru-RU locale"],
        ),
        live(
            "CurrencyPipe EUR",
            "Создайте PriceTagComponent: price = input(19.99), template {{ price() | currency:'EUR':'symbol':'1.2-2' }}.",
            """import { Component, input } from '@angular/core';
import { CurrencyPipe } from '@angular/common';

@Component({
  selector: 'app-price-tag',
  standalone: true,
  imports: [CurrencyPipe],
  template: `<span>{{ price() | currency: 'EUR' : 'symbol' : '1.2-2' }}</span>`,
})
export class PriceTagComponent {
  price = input(19.99);
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["CurrencyPipe", "EUR symbol", "input price"],
        ),
        live(
            "DecimalPipe percent",
            "Создайте RatioComponent: value = 0.756, template {{ value | number:'1.0-1' }} and {{ value | percent:'1.0-1' }}.",
            """import { Component } from '@angular/core';
import { DecimalPipe, PercentPipe } from '@angular/common';

@Component({
  selector: 'app-ratio',
  standalone: true,
  imports: [DecimalPipe, PercentPipe],
  template: `
    <p>{{ value | number: '1.0-1' }}</p>
    <p>{{ value | percent: '1.0-1' }}</p>
  `,
})
export class RatioComponent {
  value = 0.756;
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["DecimalPipe", "PercentPipe", "Format 1.0-1"],
        ),
        live(
            "JsonPipe debug",
            "Создайте DebugComponent: data = signal({ ok: true, n: 1 }), pre {{ data() | json }}.",
            """import { Component, signal } from '@angular/core';
import { JsonPipe } from '@angular/common';

@Component({
  selector: 'app-debug',
  standalone: true,
  imports: [JsonPipe],
  template: `<pre>{{ data() | json }}</pre>`,
})
export class DebugComponent {
  data = signal({ ok: true, n: 1 });
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["JsonPipe", "pre template", "signal object"],
        ),
        live(
            "SlicePipe pagination",
            "Создайте PagerComponent: items signal string[], page signal 0, "
            "template @for item of items() | slice: start:start+3.",
            """import { Component, computed, signal } from '@angular/core';
import { SlicePipe } from '@angular/common';

@Component({
  selector: 'app-pager',
  standalone: true,
  imports: [SlicePipe],
  template: `
    @for (item of items() | slice: start(): start() + 3; track item) {
      <span>{{ item }}</span>
    }
  `,
})
export class PagerComponent {
  items = signal(['a', 'b', 'c', 'd', 'e']);
  page = signal(0);
  start = computed(() => this.page() * 3);
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["SlicePipe", "computed start", "page size 3"],
        ),
        live(
            "KeyValuePipe preserveOrder",
            "Создайте MetaComponent: meta = signal({ z: 1, a: 2 }), @for entry of meta() | keyvalue.",
            """import { Component, signal } from '@angular/core';
import { KeyValuePipe } from '@angular/common';

@Component({
  selector: 'app-meta',
  standalone: true,
  imports: [KeyValuePipe],
  template: `
    @for (entry of meta() | keyvalue; track entry.key) {
      <p>{{ entry.key }}: {{ entry.value }}</p>
    }
  `,
})
export class MetaComponent {
  meta = signal({ z: 1, a: 2 });
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["KeyValuePipe", "keyvalue in @for", "signal object"],
        ),
        live(
            "TitleCasePipe",
            "Создайте HeadlineComponent: title = 'hello world', template {{ title | titlecase }}.",
            """import { Component } from '@angular/core';
import { TitleCasePipe } from '@angular/common';

@Component({
  selector: 'app-headline',
  standalone: true,
  imports: [TitleCasePipe],
  template: `<h1>{{ title | titlecase }}</h1>`,
})
export class HeadlineComponent {
  title = 'hello world';
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["TitleCasePipe", "titlecase pipe", "Standalone import"],
        ),
        live(
            "CVA с setDisabledState",
            "Создайте ToggleSwitchComponent implements ControlValueAccessor с setDisabledState(isDisabled).",
            """import { Component, forwardRef } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'app-toggle-switch',
  standalone: true,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => ToggleSwitchComponent),
    multi: true,
  }],
  template: `<button type="button" [disabled]="disabled" (click)="toggle()">{{ on ? 'ON' : 'OFF' }}</button>`,
})
export class ToggleSwitchComponent implements ControlValueAccessor {
  on = false;
  disabled = false;
  private onChange: (v: boolean) => void = () => {};

  writeValue(value: boolean) { this.on = !!value; }
  registerOnChange(fn: (v: boolean) => void) { this.onChange = fn; }
  registerOnTouched(_fn: () => void) {}
  setDisabledState(isDisabled: boolean) { this.disabled = isDisabled; }

  toggle() {
    if (this.disabled) return;
    this.on = !this.on;
    this.onChange(this.on);
  }
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["setDisabledState", "NG_VALUE_ACCESSOR", "disabled button"],
        ),
        live(
            "CVA validate method stub",
            "Создайте RatingCvaComponent с validate(): ValidationErrors | null если value < 1.",
            """import { Component, forwardRef } from '@angular/core';
import {
  AbstractControl,
  ControlValueAccessor,
  NG_VALIDATORS,
  NG_VALUE_ACCESSOR,
  ValidationErrors,
  Validator,
} from '@angular/forms';

@Component({
  selector: 'app-rating-cva',
  standalone: true,
  providers: [
    { provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => RatingCvaComponent), multi: true },
    { provide: NG_VALIDATORS, useExisting: forwardRef(() => RatingCvaComponent), multi: true },
  ],
  template: `<input type="number" [value]="value" (input)="onInput($event)" />`,
})
export class RatingCvaComponent implements ControlValueAccessor, Validator {
  value = 0;
  private onChange: (v: number) => void = () => {};

  writeValue(v: number) { this.value = v ?? 0; }
  registerOnChange(fn: (v: number) => void) { this.onChange = fn; }
  registerOnTouched(_fn: () => void) {}
  validate(_control: AbstractControl): ValidationErrors | null {
    return this.value < 1 ? { minRating: true } : null;
  }

  onInput(event: Event) {
    this.value = Number((event.target as HTMLInputElement).value);
    this.onChange(this.value);
  }
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["NG_VALIDATORS", "validate() method", "ControlValueAccessor"],
        ),
        live(
            "Pipe with multiple args",
            "Создайте PluralizePipe: transform(count: number, singular: string, plural: string).",
            """import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'pluralize', standalone: true })
export class PluralizePipe implements PipeTransform {
  transform(count: number, singular: string, plural: string): string {
    return count === 1 ? singular : plural;
  }
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["Multiple pipe args", "singular/plural", "standalone"],
        ),
        live(
            "AsyncPipe + @let",
            "Создайте OrderStatusComponent: status$ = api.status(), @let s = status$ | async; @if (s) { {{ s }} }.",
            """import { Component, inject } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { OrderApi } from './order-api';

@Component({
  selector: 'app-order-status',
  standalone: true,
  imports: [AsyncPipe],
  template: `
    @let s = status$ | async;
    @if (s) { <p>Status: {{ s }}</p> }
  `,
})
export class OrderStatusComponent {
  status$ = inject(OrderApi).status();
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["@let with async", "AsyncPipe", "@if guard"],
        ),
        live(
            "Animations trigger stub",
            "Создайте FadeComponent с animations: [trigger('fade', [transition(':enter', [style({ opacity: 0 }), animate('200ms')])])].",
            """import { Component } from '@angular/core';
import { animate, style, transition, trigger } from '@angular/animations';

@Component({
  selector: 'app-fade',
  standalone: true,
  animations: [
    trigger('fade', [
      transition(':enter', [style({ opacity: 0 }), animate('200ms', style({ opacity: 1 }))]),
    ]),
  ],
  template: `@if (show) { <p @fade>Visible</p> }`,
})
export class FadeComponent {
  show = true;
}""",
            lang="typescript",
            topic="Pipes и CVA",
            requirements=["trigger :enter", "animate 200ms", "@fade in template"],
        ),

        # ── Тестирование (119–132) ──
        live(
            "TestBed standalone component",
            "Напишите spec для CounterComponent: configureTestingModule imports [CounterComponent], "
            "click button, expect text contains '1'.",
            """import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CounterComponent } from './counter.component';

describe('CounterComponent', () => {
  let fixture: ComponentFixture<CounterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [CounterComponent] }).compileComponents();
    fixture = TestBed.createComponent(CounterComponent);
    fixture.detectChanges();
  });

  it('increments on click', () => {
    fixture.nativeElement.querySelector('button').click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('1');
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["TestBed.configureTestingModule", "imports standalone", "click + detectChanges"],
        ),
        live(
            "HttpClientTestingModule",
            "Напишите spec UserApi: HttpTestingController expectOne GET /api/users, flush mock data.",
            """import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { UserApi } from './user-api';

describe('UserApi', () => {
  let api: UserApi;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule], providers: [UserApi] });
    api = TestBed.inject(UserApi);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('loads users', () => {
    api.getUsers().subscribe(users => expect(users.length).toBe(1));
    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('GET');
    req.flush([{ id: 1, name: 'Ada' }]);
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["HttpTestingController", "expectOne + flush", "afterEach verify"],
        ),
        live(
            "Provider override in TestBed",
            "Напишите spec с overrideProvider LOGGER useValue mockLogger.",
            """import { TestBed } from '@angular/core/testing';
import { LOGGER, Logger } from './logger';
import { AppComponent } from './app.component';

describe('AppComponent', () => {
  const mockLogger: Logger = { log: jasmine.createSpy('log') };

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [AppComponent] })
      .overrideProvider(LOGGER, { useValue: mockLogger })
      .compileComponents();
  });

  it('uses mock logger', () => {
    expect(mockLogger.log).toBeDefined();
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["overrideProvider", "useValue mock", "compileComponents"],
        ),
        live(
            "spyOn service method",
            "Напишите spec: spyOn(api, 'getUser').and.returnValue(of({ id: 1, name: 'Test' })).",
            """import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { ProfileComponent } from './profile.component';
import { UserApi } from './user-api';

describe('ProfileComponent', () => {
  let fixture: ComponentFixture<ProfileComponent>;
  let api: jasmine.SpyObj<UserApi>;

  beforeEach(async () => {
    api = jasmine.createSpyObj('UserApi', ['getUser']);
    api.getUser.and.returnValue(of({ id: 1, name: 'Test' }));

    await TestBed.configureTestingModule({
      imports: [ProfileComponent],
      providers: [{ provide: UserApi, useValue: api }],
    }).compileComponents();

    fixture = TestBed.createComponent(ProfileComponent);
    fixture.detectChanges();
  });

  it('renders user name', () => {
    expect(fixture.nativeElement.textContent).toContain('Test');
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["jasmine.createSpyObj", "and.returnValue(of(...))", "Provider override"],
        ),
        live(
            "fakeAsync tick",
            "Напишите spec с fakeAsync, tick(1000), проверьте async результат.",
            """import { fakeAsync, tick } from '@angular/core/testing';
import { delay, of } from 'rxjs';

describe('DelayedLoader', () => {
  it('resolves after delay', fakeAsync(() => {
    let value = '';
    of('done').pipe(delay(1000)).subscribe(v => (value = v));
    tick(1000);
    expect(value).toBe('done');
  }));
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["fakeAsync", "tick(1000)", "delay observable"],
        ),
        live(
            "By.css DebugElement",
            "Напишите spec: By.css('button.submit'), debugElement.nativeElement.click().",
            """import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { FormComponent } from './form.component';

describe('FormComponent', () => {
  let fixture: ComponentFixture<FormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [FormComponent] }).compileComponents();
    fixture = TestBed.createComponent(FormComponent);
    fixture.detectChanges();
  });

  it('submits via submit button', () => {
    const btn = fixture.debugElement.query(By.css('button.submit'));
    btn.nativeElement.click();
    fixture.detectChanges();
    expect(fixture.componentInstance.submitted).toBeTrue();
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["By.css", "debugElement.query", "nativeElement.click"],
        ),
        live(
            "triggerEventHandler",
            "Напишите spec: debugElement.triggerEventHandler('click', null).",
            """import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { LikeButtonComponent } from './like-button.component';

describe('LikeButtonComponent', () => {
  let fixture: ComponentFixture<LikeButtonComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [LikeButtonComponent] }).compileComponents();
    fixture = TestBed.createComponent(LikeButtonComponent);
    fixture.detectChanges();
  });

  it('likes on click', () => {
    const btn = fixture.debugElement.query(By.css('button'));
    btn.triggerEventHandler('click', null);
    fixture.detectChanges();
    expect(fixture.componentInstance.liked()).toBeTrue();
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["triggerEventHandler('click')", "By.css button", "signal liked"],
        ),
        live(
            "Test output emitter",
            "Напишите spec RatingComponent: subscribe to rated output, click star, expect emitted value.",
            """import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RatingComponent } from './rating.component';

describe('RatingComponent', () => {
  let fixture: ComponentFixture<RatingComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [RatingComponent] }).compileComponents();
    fixture = TestBed.createComponent(RatingComponent);
    fixture.detectChanges();
  });

  it('emits rating', () => {
    const values: number[] = [];
    fixture.componentInstance.rated.subscribe(v => values.push(v));
    fixture.nativeElement.querySelectorAll('button')[2].click();
    expect(values).toEqual([3]);
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["Subscribe to @Output", "Emit on click", "expect values array"],
        ),
        live(
            "Test input signal",
            "Напишите spec HeadingComponent: fixture.componentRef.setInput('title', 'Hi'); detectChanges; expect text.",
            """import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HeadingComponent } from './heading.component';

describe('HeadingComponent', () => {
  let fixture: ComponentFixture<HeadingComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [HeadingComponent] }).compileComponents();
    fixture = TestBed.createComponent(HeadingComponent);
  });

  it('renders input title', () => {
    fixture.componentRef.setInput('title', 'Hi');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Hi');
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["componentRef.setInput", "input.required title", "detectChanges"],
        ),
        live(
            "Test functional guard",
            "Напишите spec authGuard: TestBed.runInInjectionContext(() => authGuard(route, state)).",
            """import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from './auth.service';

describe('authGuard', () => {
  it('allows logged in user', () => {
    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: { isLoggedIn: () => true } },
        { provide: Router, useValue: { parseUrl: (u: string) => u } },
      ],
    });
    const result = TestBed.runInInjectionContext(() => authGuard({} as any, {} as any));
    expect(result).toBeTrue();
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["runInInjectionContext", "Mock AuthService", "CanActivateFn test"],
        ),
        live(
            "Test pipe in isolation",
            "Напишите spec CapitalizePipe: new CapitalizePipe().transform('angular') === 'Angular'.",
            """import { CapitalizePipe } from './capitalize.pipe';

describe('CapitalizePipe', () => {
  const pipe = new CapitalizePipe();

  it('capitalizes first letter', () => {
    expect(pipe.transform('angular')).toBe('Angular');
  });

  it('handles empty string', () => {
    expect(pipe.transform('')).toBe('');
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["Instantiate pipe directly", "transform assertions", "Empty string case"],
        ),
        live(
            "Test interceptor",
            "Напишите spec authInterceptor: TestBed inject HttpClient, expectOne with Authorization header.",
            """import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: 'TOKEN', useValue: 'secret' },
      ],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('adds Authorization header', () => {
    http.get('/api/me').subscribe();
    const req = httpMock.expectOne('/api/me');
    expect(req.request.headers.has('Authorization')).toBeTrue();
    req.flush({});
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["withInterceptors in test", "expectOne headers", "provideHttpClientTesting"],
        ),
        live(
            "RouterTestingHarness",
            "Напишите spec с RouterTestingHarness.create() navigate to /products.",
            """import { TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { Router } from '@angular/router';
import { routes } from './app.routes';

describe('Router navigation', () => {
  it('navigates to products', async () => {
    TestBed.configureTestingModule({ imports: [RouterTestingModule.withRoutes(routes)] });
    const router = TestBed.inject(Router);
    await router.navigate(['/products']);
    expect(router.url).toContain('/products');
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["RouterTestingModule.withRoutes", "navigate async", "router.url assert"],
        ),
        live(
            "ComponentFixture whenStable",
            "Напишите spec async: await fixture.whenStable() после HTTP load в ngOnInit.",
            """import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { UserListComponent } from './user-list.component';

describe('UserListComponent', () => {
  let fixture: ComponentFixture<UserListComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserListComponent, HttpClientTestingModule],
    }).compileComponents();
    fixture = TestBed.createComponent(UserListComponent);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('loads users async', async () => {
    fixture.detectChanges();
    httpMock.expectOne('/api/users').flush([{ id: 1, name: 'Ada' }]);
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Ada');
  });
});""",
            lang="typescript",
            topic="Тестирование",
            requirements=["whenStable()", "flush after detectChanges", "Async HTTP load"],
        ),
    ]

// Помощники фоновых опросов сервера (панели «Настроек»: видеотека, база знаний, колоды, модели).

/** Ответ сервера не изменился — незачем перерисовывать дерево (списки тут до тысяч строк). */
export function sameJson(a, b) {
  if (a === b) return true;
  try {
    return JSON.stringify(a) === JSON.stringify(b);
  } catch {
    return false;
  }
}

/**
 * Сохранить ответ опроса, не вызывая перерисовки при тех же данных.
 * set — setState из useState.
 */
export function setIfChanged(set, next) {
  set((prev) => (sameJson(prev, next) ? prev : next));
}

/**
 * Пауза до следующего опроса: скрытое окно не опрашиваем — в десктоп-приложении
 * backgroundThrottling выключен, иначе фоновые вкладки грузят процессор бесконечно.
 */
export function nextDelay(ms) {
  return document.hidden ? Math.min(Math.max(ms, 5000), 30000) : ms;
}

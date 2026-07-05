let selectedDeckId = null;
let selectedDeckHasTopics = false;
let decksById = {};
let pendingMode = "due";
let sessionId = null;
let autoAdvanceTimer = null;
let needsCode = false;
let needsMath = false;
let codeEditorTheme = "light";

const $ = (id) => document.getElementById(id);

function usesEditor() {
  return needsCode || needsMath;
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

function showHome() {
  clearTimeout(autoAdvanceTimer);
  sessionId = null;
  CodeEditor.hide();
  MathEditor.hide();
  $("home-view").classList.remove("hidden");
  $("topic-view").classList.add("hidden");
  $("study-view").classList.add("hidden");
  loadDecks();
}

function showTopicPicker() {
  $("home-view").classList.add("hidden");
  $("topic-view").classList.remove("hidden");
  $("study-view").classList.add("hidden");
}

function showStudy() {
  $("home-view").classList.add("hidden");
  $("topic-view").classList.add("hidden");
  $("study-view").classList.remove("hidden");
}

const MODE_LABELS = {
  due: "повторение",
  new: "новые",
  weak: "слабые",
  all: "вся колода",
};

async function loadConfig() {
  const c = await api("/api/config");
  $("session_limit").value = c.session_limit;
  $("session_limit").max = c.session_limit_max;
  $("pass_score").value = c.pass_score;
  $("max_follow_ups").value = c.max_follow_ups;
  $("auto_advance_sec").value = c.auto_advance_sec;
  $("auto_advance_sec").max = c.auto_advance_max_sec;
  $("ollama_url").value = c.ollama_url;
  $("model").value = c.model;
  $("api_key").value = c.api_key;
  $("timeout").value = c.timeout;
  $("asr_url").value = c.asr_url || "";
  $("asr_user").value = c.asr_user || "";
  $("asr_password").value = c.asr_password || "";
  $("asr_language").value = c.asr_language || "ru";
  codeEditorTheme = c.code_editor_theme === "dark" ? "dark" : "light";
  $("code_editor_theme").value = codeEditorTheme;
  CodeEditor.setTheme(codeEditorTheme);
}

async function saveConfig() {
  await api("/api/config", {
    method: "POST",
    body: JSON.stringify({
      session_limit: +$("session_limit").value,
      pass_score: +$("pass_score").value,
      max_follow_ups: +$("max_follow_ups").value,
      auto_advance_sec: +$("auto_advance_sec").value,
      ollama_url: $("ollama_url").value.trim(),
      model: $("model").value.trim(),
      api_key: $("api_key").value.trim(),
      timeout: +$("timeout").value,
      asr_url: $("asr_url").value.trim(),
      asr_user: $("asr_user").value.trim(),
      asr_password: $("asr_password").value.trim(),
      asr_language: $("asr_language").value.trim() || "ru",
      code_editor_theme: $("code_editor_theme").value,
    }),
  });
  codeEditorTheme = $("code_editor_theme").value === "dark" ? "dark" : "light";
  CodeEditor.setTheme(codeEditorTheme);
  $("settings-msg").textContent = "Сохранено";
  setTimeout(() => ($("settings-msg").textContent = ""), 2000);
}

async function testOllama() {
  const r = await api("/api/ollama/test", { method: "POST" });
  $("settings-msg").textContent = r.detail;
  $("settings-msg").className = r.ok ? "muted" : "error";
}

function startDueStudy() {
  requestStudy("due").catch((e) => alert(e.message));
}

function bindDeckRow(tr, deckId) {
  tr.onclick = () => selectDeck(deckId);
  tr.ondblclick = () => {
    selectDeck(deckId);
    startDueStudy();
  };
}

function bindDeckCard(card, deckId) {
  card.onclick = () => selectDeck(deckId);
  card.ondblclick = () => {
    selectDeck(deckId);
    startDueStudy();
  };
}

function selectDeck(deckId) {
  selectedDeckId = deckId;
  selectedDeckHasTopics = !!(decksById[deckId]?.has_topics);
  $("decks-table").querySelectorAll("tr").forEach((r) => {
    r.classList.toggle("selected", r.dataset.deckId === deckId);
  });
  $("decks-list").querySelectorAll(".deck-card").forEach((c) => {
    c.classList.toggle("selected", c.dataset.deckId === deckId);
  });
}

async function loadDecks() {
  const { decks } = await api("/api/decks");
  decksById = {};
  const tbody = $("decks-table").querySelector("tbody");
  const list = $("decks-list");
  tbody.innerHTML = "";
  list.innerHTML = "";
  decks.forEach((d) => {
    if (!d.error) decksById[d.deck_id] = d;
    const tr = document.createElement("tr");
    tr.dataset.deckId = d.deck_id;
    if (d.error) {
      tr.innerHTML = `<td>${d.name}</td><td colspan="7" class="error">${d.error}</td>`;
      const card = document.createElement("div");
      card.className = "deck-card";
      card.innerHTML = `<div class="deck-card-title">${d.name}</div><div class="error">${d.error}</div>`;
      list.appendChild(card);
    } else {
      tr.innerHTML = `
        <td>${d.name}</td><td>${d.total}</td><td>${d.mastered}</td><td>${d.passed_today}</td>
        <td>${d.due}</td><td>${d.new}</td><td>${d.weak}</td>
        <td>${d.studied ? d.avg_score : "—"}</td>`;
      bindDeckRow(tr, d.deck_id);

      const card = document.createElement("div");
      card.className = "deck-card";
      card.dataset.deckId = d.deck_id;
      card.innerHTML = `
        <div class="deck-card-title">${d.name}</div>
        <div class="deck-card-stats">
          <span>Всего ${d.total}</span>
          <span>Усвоено ${d.mastered}</span>
          <span>Сегодня ${d.passed_today}</span>
          <span>К повтору ${d.due}</span>
          <span>Новые ${d.new}</span>
          <span>Слабые ${d.weak}</span>
          <span>Ср. ${d.studied ? d.avg_score : "—"}</span>
        </div>`;
      bindDeckCard(card, d.deck_id);
      list.appendChild(card);
    }
    tbody.appendChild(tr);
  });
  if (decks.length && !selectedDeckId && !decks[0].error) {
    selectDeck(decks[0].deck_id);
  } else if (selectedDeckId && decksById[selectedDeckId]) {
    selectedDeckHasTopics = !!decksById[selectedDeckId].has_topics;
  }
}

async function openTopicPicker(mode) {
  if (!selectedDeckId) {
    alert("Выберите колоду");
    return;
  }
  pendingMode = mode;
  const data = await api(`/api/deck/${selectedDeckId}/topics`);
  $("topic-deck-title").textContent = data.name;
  $("topic-mode-label").textContent = `Режим: ${MODE_LABELS[mode] || mode}`;
  const list = $("topics-list");
  list.innerHTML = "";
  data.topics.forEach((t) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "topic-card";
    btn.innerHTML = `
      <div class="topic-card-title">${t.name}</div>
      <div class="topic-card-stats">
        всего ${t.total} · к повтору ${t.due} · новые ${t.new} · слабые ${t.weak}
      </div>`;
    btn.onclick = () => startMode(mode, t.name).catch((e) => alert(e.message));
    list.appendChild(btn);
  });
  showTopicPicker();
}

async function requestStudy(mode) {
  if (!selectedDeckId) {
    alert("Выберите колоду");
    return;
  }
  if (selectedDeckHasTopics) {
    await openTopicPicker(mode);
    return;
  }
  await startMode(mode);
}

function updateStats(stats) {
  $("study-stats").textContent =
    `Сегодня ${stats.passed_today} · Усвоено ${stats.mastered}/${stats.total} · ` +
    `к повтору ${stats.due} · сессия ${stats.index}/${stats.queue}`;
}

async function showCard(card) {
  if (!card) {
    $("question").textContent = "Нет карточек для выбранного режима.";
    CodeEditor.hide();
    MathEditor.hide();
    VoiceInput.setVisible(false);
    $("answer-text").classList.add("hidden");
    $("btn-submit").disabled = true;
    return;
  }

  needsCode = card.needs_code;
  needsMath = card.needs_math;

  if (needsMath) {
    $("answer-text").classList.add("hidden");
    VoiceInput.setVisible(false);
    CodeEditor.hide();
    MathEditor.clear();
    const qText = card.topic ? `[${card.topic}]\n\n${card.question}` : card.question;
    await MathEditor.renderQuestion($("question"), qText);
    await MathEditor.show(card.math_starter || "");
    $("answer-label").textContent = "Редактор формул LaTeX — введите решение";
    $("status").textContent =
      `лучший ${card.best_score} · попыток ${card.attempts} · Ctrl+Enter — проверить`;
  } else if (needsCode) {
    MathEditor.hide();
    $("answer-text").classList.add("hidden");
    VoiceInput.setVisible(false);
    const qParts = [card.question];
    if (card.topic) qParts.unshift(`[${card.topic}]`);
    $("question").textContent = qParts.join("\n");
    CodeEditor.clear();
    await CodeEditor.show(card.language || "typescript", codeEditorTheme);
    $("answer-label").textContent = card.is_live_code
      ? "Редактор кода — напишите решение"
      : "Редактор кода — исправьте или дополните";
    $("status").textContent =
      `лучший ${card.best_score} · попыток ${card.attempts} · Ctrl+Space — подсказки · Ctrl+Enter — проверить`;
  } else {
    CodeEditor.hide();
    MathEditor.hide();
    $("answer-text").classList.remove("hidden");
    $("answer-text").value = "";
    $("question").textContent = card.question;
    VoiceInput.setVisible(true);
    $("answer-label").textContent = "Ваш ответ (своими словами)";
    $("status").textContent =
      `лучший ${card.best_score} · попыток ${card.attempts} · 🎤 — ответ голосом`;
  }

  $("btn-submit").disabled = false;
  $("btn-next").disabled = true;
  $("btn-hint").disabled = false;
  $("feedback").textContent = "";
}

function getAnswer() {
  if (needsCode) return CodeEditor.getValue().trim();
  if (needsMath) return MathEditor.getValue().trim();
  return $("answer-text").value.trim();
}

function clearAnswer() {
  if (needsCode) CodeEditor.clear();
  else if (needsMath) MathEditor.clear();
  else $("answer-text").value = "";
}

async function startMode(mode, topic = "") {
  if (!selectedDeckId) {
    alert("Выберите колоду");
    return;
  }
  clearTimeout(autoAdvanceTimer);
  const payload = { deck_id: selectedDeckId, mode };
  if (topic) payload.topic = topic;
  const data = await api("/api/session", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  sessionId = data.session_id;
  $("study-title").textContent = `${data.deck_name} · ${data.mode}`;
  updateStats(data.stats);
  showStudy();
  if (data.empty) await showCard(null);
  else await showCard(data.card);
}

async function submitAnswer() {
  if (!sessionId) return;
  $("btn-submit").disabled = true;
  $("btn-hint").disabled = true;
  if (!usesEditor()) $("btn-voice").disabled = true;
  $("status").textContent = "Ollama думает…";
  try {
    const r = await api(`/api/session/${sessionId}/answer`, {
      method: "POST",
      body: JSON.stringify({ answer: getAnswer() }),
    });
    $("feedback").textContent = r.feedback;
    updateStats(r.stats);
    $("btn-next").disabled = false;
    $("btn-submit").disabled = !r.can_submit;
    $("btn-hint").disabled = false;
    if (!usesEditor()) $("btn-voice").disabled = false;
    if (r.clear_answer && !usesEditor()) {
      $("answer-text").value = "";
    } else if (r.finalize) {
      clearAnswer();
    }
    if (r.auto_advance_ms > 0) {
      $("status").textContent = `Следующая через ${r.auto_advance_ms / 1000} с…`;
      autoAdvanceTimer = setTimeout(nextCard, r.auto_advance_ms);
    } else if (!r.can_submit) {
      $("status").textContent = r.clear_answer
        ? "Ответьте на уточняющий вопрос (можно голосом)."
        : needsMath
          ? "Внесите правки в формулу и отправьте снова или нажмите «Следующая →»."
          : "Внесите правки и отправьте снова или нажмите «Следующая →».";
    } else {
      $("status").textContent = "";
    }
  } catch (e) {
    $("feedback").textContent = "❌ " + e.message;
    $("btn-submit").disabled = false;
    $("btn-hint").disabled = false;
    if (!usesEditor()) $("btn-voice").disabled = false;
    $("status").textContent = "";
  }
}

async function nextCard() {
  clearTimeout(autoAdvanceTimer);
  if (!sessionId) return;
  const r = await api(`/api/session/${sessionId}/next`, { method: "POST" });
  if (r.done) {
    alert("Сессия завершена");
    showHome();
    return;
  }
  updateStats(r.stats);
  await showCard(r.card);
}

async function showHint() {
  if (!sessionId) return;
  $("btn-hint").disabled = true;
  $("status").textContent = "Запрашиваем подсказку…";
  try {
    const r = await api(`/api/session/${sessionId}/hint`, {
      method: "POST",
      body: JSON.stringify({ draft: getAnswer() }),
    });
    if (r.hint) {
      const fb = $("feedback");
      if (!fb.textContent.includes(r.hint)) {
        fb.textContent += (fb.textContent.trim() ? "\n\n" : "") + "💡 " + r.hint;
      }
    }
    $("status").textContent = fbHasReview($("feedback").textContent)
      ? ""
      : "Подсказка получена. Отправьте ответ, когда будете готовы.";
  } catch (e) {
    const fb = $("feedback");
    fb.textContent += (fb.textContent.trim() ? "\n\n" : "") + "❌ Подсказка: " + e.message;
    $("status").textContent = "";
  }
  $("btn-hint").disabled = false;
}

function fbHasReview(text) {
  return /Оценка:\s*\d+\/100/.test(text);
}

$("btn-save").onclick = () => saveConfig().catch((e) => alert(e.message));
$("btn-test").onclick = () => testOllama().catch((e) => alert(e.message));
$("btn-due").onclick = startDueStudy;
$("btn-new").onclick = () => requestStudy("new").catch((e) => alert(e.message));
$("btn-weak").onclick = () => requestStudy("weak").catch((e) => alert(e.message));
$("btn-all").onclick = () => requestStudy("all").catch((e) => alert(e.message));
$("btn-topic-back").onclick = showHome;
$("btn-back").onclick = showHome;
$("btn-submit").onclick = submitAnswer;
$("btn-next").onclick = nextCard;
$("btn-hint").onclick = showHint;

document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter" && !usesEditor()) submitAnswer();
});

document.getElementById("code-editor-host").addEventListener("code-submit", () => {
  if (needsCode) submitAnswer();
});

document.getElementById("math-editor-wrap").addEventListener("math-submit", () => {
  if (needsMath) submitAnswer();
});

VoiceInput.bind($("btn-voice"), $("answer-text"), (text) => {
  $("status").textContent = text;
});

loadConfig().catch(console.error);
loadDecks().catch(console.error);

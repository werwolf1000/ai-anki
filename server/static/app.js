let selectedDeckId = null;
let sessionId = null;
let autoAdvanceTimer = null;
let needsCode = false;

const $ = (id) => document.getElementById(id);

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
  $("home-view").classList.remove("hidden");
  $("study-view").classList.add("hidden");
  loadDecks();
}

function showStudy() {
  $("home-view").classList.add("hidden");
  $("study-view").classList.remove("hidden");
}

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
    }),
  });
  $("settings-msg").textContent = "Сохранено";
  setTimeout(() => ($("settings-msg").textContent = ""), 2000);
}

async function testOllama() {
  const r = await api("/api/ollama/test", { method: "POST" });
  $("settings-msg").textContent = r.detail;
  $("settings-msg").className = r.ok ? "muted" : "error";
}

function selectDeck(deckId) {
  selectedDeckId = deckId;
  $("decks-table").querySelectorAll("tr").forEach((r) => {
    r.classList.toggle("selected", r.dataset.deckId === deckId);
  });
  $("decks-list").querySelectorAll(".deck-card").forEach((c) => {
    c.classList.toggle("selected", c.dataset.deckId === deckId);
  });
}

async function loadDecks() {
  const { decks } = await api("/api/decks");
  const tbody = $("decks-table").querySelector("tbody");
  const list = $("decks-list");
  tbody.innerHTML = "";
  list.innerHTML = "";
  decks.forEach((d) => {
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
      tr.onclick = () => selectDeck(d.deck_id);

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
      card.onclick = () => selectDeck(d.deck_id);
      list.appendChild(card);
    }
    tbody.appendChild(tr);
  });
  if (decks.length && !selectedDeckId && !decks[0].error) {
    selectDeck(decks[0].deck_id);
  }
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
    VoiceInput.setVisible(false);
    $("answer-text").classList.add("hidden");
    $("btn-submit").disabled = true;
    return;
  }
  $("question").textContent = card.question;
  needsCode = card.needs_code;
  if (needsCode) {
    $("answer-text").classList.add("hidden");
    VoiceInput.setVisible(false);
    CodeEditor.clear();
    await CodeEditor.show(card.language || "typescript");
  } else {
    CodeEditor.hide();
    $("answer-text").classList.remove("hidden");
    $("answer-text").value = "";
    VoiceInput.setVisible(true);
  }
  $("answer-label").textContent = needsCode
    ? (card.is_live_code ? "Редактор кода — напишите решение" : "Редактор кода — исправьте или дополните")
    : "Ваш ответ (своими словами)";
  $("btn-submit").disabled = false;
  $("btn-next").disabled = true;
  $("btn-hint").disabled = false;
  $("feedback").textContent = "";
  $("status").textContent = needsCode
    ? `лучший ${card.best_score} · попыток ${card.attempts} · Ctrl+Space — подсказки · Ctrl+Enter — проверить`
    : `лучший ${card.best_score} · попыток ${card.attempts} · 🎤 — ответ голосом`;
}

function getAnswer() {
  return needsCode ? CodeEditor.getValue().trim() : $("answer-text").value.trim();
}

function clearAnswer() {
  if (needsCode) CodeEditor.clear();
  else $("answer-text").value = "";
}

async function startMode(mode) {
  if (!selectedDeckId) {
    alert("Выберите колоду");
    return;
  }
  clearTimeout(autoAdvanceTimer);
  const data = await api("/api/session", {
    method: "POST",
    body: JSON.stringify({ deck_id: selectedDeckId, mode }),
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
  if (!needsCode) $("btn-voice").disabled = true;
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
    if (!needsCode) $("btn-voice").disabled = false;
    if (r.clear_answer && !needsCode) {
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
        : "Внесите правки и отправьте снова или нажмите «Следующая →».";
    } else {
      $("status").textContent = "";
    }
  } catch (e) {
    $("feedback").textContent = "❌ " + e.message;
    $("btn-submit").disabled = false;
    $("btn-hint").disabled = false;
    if (!needsCode) $("btn-voice").disabled = false;
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
$("btn-due").onclick = () => startMode("due").catch((e) => alert(e.message));
$("btn-new").onclick = () => startMode("new").catch((e) => alert(e.message));
$("btn-weak").onclick = () => startMode("weak").catch((e) => alert(e.message));
$("btn-all").onclick = () => startMode("all").catch((e) => alert(e.message));
$("btn-back").onclick = showHome;
$("btn-submit").onclick = submitAnswer;
$("btn-next").onclick = nextCard;
$("btn-hint").onclick = showHint;

document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter" && !needsCode) submitAnswer();
});

document.getElementById("code-editor-host").addEventListener("code-submit", () => {
  if (needsCode) submitAnswer();
});

VoiceInput.bind($("btn-voice"), $("answer-text"), (text) => {
  $("status").textContent = text;
});

loadConfig().catch(console.error);
loadDecks().catch(console.error);

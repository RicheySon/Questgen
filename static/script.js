const form = document.getElementById("generator-form");
const subjectSelect = document.getElementById("subject");
const timeNote = document.getElementById("time-note");

const setupScreen = document.getElementById("setup-screen");
const quizScreen = document.getElementById("quiz-screen");
const resultScreen = document.getElementById("result-screen");

const questionList = document.getElementById("question-list");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");
const subjectChip = document.getElementById("subject-chip");
const difficultyChip = document.getElementById("difficulty-chip");
const focusChip = document.getElementById("focus-chip");
const timerBox = document.getElementById("timer-box");
const timerLabel = document.getElementById("quiz-timer");

const submitBtn = document.getElementById("submit-btn");
const exportJsonBtn = document.getElementById("export-json-btn");
const exportCsvBtn = document.getElementById("export-csv-btn");
const shareBtn = document.getElementById("share-btn");

const feedbackList = document.getElementById("feedback-list");
const scoreRing = document.getElementById("score-ring");
const resultScore = document.getElementById("result-score");
const resultCount = document.getElementById("result-count");
const resultMessage = document.getElementById("result-message");
const nextDifficulty = document.getElementById("next-difficulty");
const retakeBtn = document.getElementById("retake-btn");
const resultExportJson = document.getElementById("result-export-json");
const resultPdfBtn = document.getElementById("result-pdf");

let currentQuiz = [];
let currentSubjectLabel = "";
let currentDifficulty = "";
let lastResult = null;
let quizDuration = 0;
let timerId = null;
let startedAt = null;

function showScreen(screen) {
  [setupScreen, quizScreen, resultScreen].forEach((s) => s.classList.add("hidden"));
  screen.classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function escapeHtml(raw) {
  return String(raw)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatTime(totalSeconds) {
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

/* ---------- Subjects ---------- */
async function loadSubjects() {
  try {
    const res = await fetch("/api/subjects");
    const data = await res.json();
    subjectSelect.innerHTML = "";
    data.subjects.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.value;
      opt.textContent = s.label;
      subjectSelect.appendChild(opt);
    });
  } catch (err) {
    console.error("Failed to load subjects", err);
    subjectSelect.innerHTML = '<option value="science">Science</option>';
  }
}

/* ---------- Timer ---------- */
function updateTimer() {
  if (!startedAt || quizDuration <= 0) {
    timerLabel.textContent = "00:00";
    return;
  }
  const elapsed = Math.floor((Date.now() - startedAt) / 1000);
  const remaining = Math.max(0, quizDuration - elapsed);
  timerLabel.textContent = formatTime(remaining);

  timerBox.classList.toggle("warning", remaining <= 15 && remaining > 0);

  if (remaining === 0) {
    clearInterval(timerId);
    timerId = null;
    timerBox.classList.remove("warning");
    autoSubmitOnTimeout();
  }
}

function startTimer(seconds) {
  clearInterval(timerId);
  quizDuration = seconds;
  startedAt = Date.now();
  updateTimer();
  timerId = setInterval(updateTimer, 1000);
}

function stopTimer() {
  clearInterval(timerId);
  timerId = null;
  timerBox.classList.remove("warning");
}

/* ---------- Progress ---------- */
function selectedAnswerCount() {
  let count = 0;
  currentQuiz.forEach((q) => {
    if (q.question_type === "short_answer") {
      const text = document.querySelector(`textarea[name="q_${q.id}"]`)?.value?.trim();
      if (text) count += 1;
    } else {
      if (document.querySelector(`input[name="q_${q.id}"]:checked`)) count += 1;
    }
  });
  return count;
}

function updateProgress() {
  const answered = selectedAnswerCount();
  const total = currentQuiz.length;
  const pct = total > 0 ? (answered / total) * 100 : 0;
  progressBar.style.width = `${pct}%`;
  progressText.textContent = `${answered} / ${total}`;
}

/* ---------- Render questions ---------- */
function renderQuestion(question) {
  const card = document.createElement("article");
  card.className = "question-card";

  const meta = document.createElement("p");
  meta.className = "question-meta";
  meta.textContent = `Question ${question.id} · ${question.question_type.replace("_", " ")} · ${question.difficulty}`;
  card.appendChild(meta);

  const prompt = document.createElement("p");
  prompt.className = "question-prompt";
  prompt.innerHTML = escapeHtml(question.prompt);
  card.appendChild(prompt);

  if (question.question_type === "short_answer") {
    const textarea = document.createElement("textarea");
    textarea.name = `q_${question.id}`;
    textarea.rows = 2;
    textarea.placeholder = "Type your answer...";
    card.appendChild(textarea);
  } else {
    const choices = document.createElement("div");
    choices.className = "choices";
    (question.choices || []).forEach((choice) => {
      const label = document.createElement("label");
      label.className = "choice";
      label.innerHTML = `
        <input type="radio" name="q_${question.id}" value="${escapeHtml(choice)}" />
        <span>${escapeHtml(choice)}</span>
      `;
      choices.appendChild(label);
    });
    card.appendChild(choices);
  }

  card.addEventListener("change", updateProgress);
  card.addEventListener("input", updateProgress);
  return card;
}

function collectAnswers() {
  return currentQuiz.map((q) => {
    if (q.question_type === "short_answer") {
      return document.querySelector(`textarea[name="q_${q.id}"]`)?.value?.trim() || "";
    }
    return document.querySelector(`input[name="q_${q.id}"]:checked`)?.value || "";
  });
}

/* ---------- Results ---------- */
function performanceLabel(pct) {
  if (pct >= 90) return "Excellent";
  if (pct >= 70) return "Great";
  if (pct >= 50) return "Good";
  if (pct >= 30) return "Keep going";
  return "Needs work";
}

function renderResults(result) {
  lastResult = result;
  const pct = result.score_percent;
  resultScore.textContent = `${pct}%`;
  resultCount.textContent = `${result.correct_count} / ${result.total}`;
  resultMessage.textContent = performanceLabel(pct);
  nextDifficulty.textContent = result.next_difficulty;

  scoreRing.style.background = pct >= 50 ? "var(--success)" : "var(--danger)";

  feedbackList.innerHTML = "";
  result.feedback.forEach((item) => {
    const div = document.createElement("div");
    div.className = `feedback-item ${item.is_correct ? "correct" : "incorrect"}`;
    const yourAnswer = item.your_answer ? escapeHtml(item.your_answer) : "(no answer)";
    div.innerHTML = `
      <div class="feedback-top">
        <p class="feedback-title">Q${item.id}. ${escapeHtml(item.question)}</p>
        <span class="verdict ${item.is_correct ? "correct" : "incorrect"}">${item.is_correct ? "Correct" : "Wrong"}</span>
      </div>
      <p class="answer-row ${item.is_correct ? "good" : "bad"}"><span class="label">Your answer:</span> <span class="value">${yourAnswer}</span></p>
      ${item.is_correct ? "" : `<p class="answer-row good"><span class="label">Correct answer:</span> <span class="value">${escapeHtml(item.expected_answer)}</span></p>`}
      <p class="explain">${escapeHtml(item.explanation)}</p>
    `;
    feedbackList.appendChild(div);
  });

  showScreen(resultScreen);
}

async function submitAnswers() {
  if (!currentQuiz.length) return;
  stopTimer();

  const res = await fetch("/api/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ questions: currentQuiz, answers: collectAnswers() }),
  });

  if (!res.ok) {
    const message = await res.text();
    alert(`Submit failed: ${message}`);
    return;
  }

  renderResults(await res.json());
}

function autoSubmitOnTimeout() {
  submitAnswers().catch((err) => {
    console.error(err);
    alert("Timer finished, but auto-submit failed.");
  });
}

/* ---------- Export / Share ---------- */
function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function toCsv(questions) {
  const header = ["id", "type", "difficulty", "prompt", "choices", "answer"];
  const rows = questions.map((q) => [
    q.id,
    q.question_type,
    q.difficulty,
    q.prompt.replaceAll('"', '""'),
    (q.choices || []).join(" | ").replaceAll('"', '""'),
    q.answer.replaceAll('"', '""'),
  ]);
  return [header.join(","), ...rows.map((r) => r.map((v) => `"${v}"`).join(","))].join("\n");
}

function exportJson() {
  if (!currentQuiz.length) return alert("Generate a quiz first.");
  downloadFile(JSON.stringify(currentQuiz, null, 2), "questgen-questions.json", "application/json");
}

function exportCsv() {
  if (!currentQuiz.length) return alert("Generate a quiz first.");
  downloadFile(toCsv(currentQuiz), "questgen-questions.csv", "text/csv");
}

async function shareQuiz() {
  if (!currentQuiz.length) return alert("Generate a quiz first.");
  const shareData = {
    title: "QuestGen Quiz",
    text: `Try this ${currentSubjectLabel} quiz with ${currentQuiz.length} questions!`,
    url: `${window.location.origin}?quiz=${encodeURIComponent(btoa(unescape(encodeURIComponent(JSON.stringify(currentQuiz)))))}`,
  };
  if (navigator.share) {
    try {
      await navigator.share(shareData);
      return;
    } catch (err) {
      console.warn("Share canceled", err);
    }
  }
  try {
    await navigator.clipboard.writeText(shareData.url);
    alert("Share link copied to clipboard.");
  } catch {
    prompt("Copy this share link:", shareData.url);
  }
}

function downloadResultPdf() {
  if (!lastResult) return alert("Submit a quiz first to download your result sheet.");
  if (!window.jspdf || !window.jspdf.jsPDF) {
    return alert("PDF library failed to load. Check your internet connection and try again.");
  }

  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: "pt", format: "a4" });

  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  const margin = 40;
  const textW = pageW - margin * 2;
  let y = margin;

  const green = [22, 163, 74];
  const red = [220, 38, 38];
  const dark = [26, 31, 54];
  const muted = [107, 115, 144];

  function ensureSpace(needed) {
    if (y + needed > pageH - margin) {
      doc.addPage();
      y = margin;
    }
  }

  doc.setTextColor(...dark);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.text("QuestGen - Result Sheet", margin, y);
  y += 18;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(...muted);
  doc.text("Built by Rejoice Akosua Dzanku", margin, y);
  y += 22;

  doc.setTextColor(...dark);
  doc.setFontSize(11);
  const meta = [
    `Topic: ${currentSubjectLabel || "-"}`,
    `Difficulty: ${currentDifficulty || "-"}`,
    `Score: ${lastResult.score_percent}%  (${lastResult.correct_count}/${lastResult.total} correct)`,
    `Suggested next level: ${lastResult.next_difficulty}`,
  ];
  meta.forEach((line) => {
    doc.text(line, margin, y);
    y += 15;
  });

  y += 6;
  doc.setDrawColor(220);
  doc.line(margin, y, pageW - margin, y);
  y += 18;

  lastResult.feedback.forEach((item) => {
    const verdict = item.is_correct ? "CORRECT" : "WRONG";
    const color = item.is_correct ? green : red;

    const questionLines = doc.splitTextToSize(`Q${item.id}. ${item.question}`, textW);
    ensureSpace(questionLines.length * 14 + 50);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(...color);
    doc.text(`[${verdict}]`, margin, y);
    y += 14;

    doc.setTextColor(...dark);
    doc.text(questionLines, margin, y);
    y += questionLines.length * 14;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    const your = doc.splitTextToSize(`Your answer: ${item.your_answer || "(no answer)"}`, textW);
    doc.setTextColor(...color);
    doc.text(your, margin, y);
    y += your.length * 13;

    if (!item.is_correct) {
      const correct = doc.splitTextToSize(`Correct answer: ${item.expected_answer}`, textW);
      doc.setTextColor(...green);
      doc.text(correct, margin, y);
      y += correct.length * 13;
    }

    const expl = doc.splitTextToSize(`Note: ${item.explanation}`, textW);
    doc.setTextColor(...muted);
    doc.text(expl, margin, y);
    y += expl.length * 13 + 12;
  });

  doc.save("questgen-result-sheet.pdf");
}

/* ---------- Events ---------- */
form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    subject: subjectSelect.value,
    total_questions: Number(document.getElementById("total_questions").value),
    difficulty: document.getElementById("difficulty").value,
    focus_topic: document.getElementById("focus_topic").value,
    include_multiple_choice: document.getElementById("multiple_choice").checked,
    include_short_answer: document.getElementById("short_answer").checked,
    include_true_false: document.getElementById("true_false").checked,
  };

  if (!payload.include_multiple_choice && !payload.include_short_answer && !payload.include_true_false) {
    return alert("Select at least one question type.");
  }

  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const message = await res.text();
    return alert(`Generate failed: ${message}`);
  }

  const data = await res.json();
  currentQuiz = data.questions;
  currentSubjectLabel = data.subject_label;
  currentDifficulty = data.adjusted_difficulty;

  subjectChip.textContent = data.subject_label;
  difficultyChip.textContent = `${data.adjusted_difficulty} level`;

  if (data.focus_topic) {
    focusChip.textContent = `Focus: ${data.focus_topic} (${data.focus_matched}/${currentQuiz.length} matched)`;
    focusChip.classList.remove("hidden");
    if (data.focus_matched === 0) {
      alert(`No questions specifically matched "${data.focus_topic}" in this category, so the quiz uses general ${data.subject_label} questions. Try a broader keyword.`);
    }
  } else {
    focusChip.classList.add("hidden");
  }

  questionList.innerHTML = "";
  currentQuiz.forEach((q) => questionList.appendChild(renderQuestion(q)));

  showScreen(quizScreen);
  updateProgress();
  startTimer(data.recommended_seconds);
});

submitBtn.addEventListener("click", () => {
  const answered = selectedAnswerCount();
  if (answered < currentQuiz.length) {
    const ok = confirm(`You answered ${answered} of ${currentQuiz.length}. Submit anyway?`);
    if (!ok) return;
  }
  submitAnswers().catch((err) => {
    console.error(err);
    alert("Submit failed.");
  });
});

retakeBtn.addEventListener("click", () => {
  currentQuiz = [];
  stopTimer();
  showScreen(setupScreen);
});

exportJsonBtn.addEventListener("click", exportJson);
exportCsvBtn.addEventListener("click", exportCsv);
shareBtn.addEventListener("click", shareQuiz);
resultExportJson.addEventListener("click", exportJson);
resultPdfBtn.addEventListener("click", downloadResultPdf);

loadSubjects();

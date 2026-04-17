<template>
  <Teleport to="body">
    <!-- Floating toggle button -->
    <button
      v-if="!showPanel"
      class="ai-chat-toggle"
      @click="showPanel = true"
      title="AI Assistant"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z"
        />
        <line x1="10" y1="22" x2="14" y2="22" />
      </svg>
    </button>

    <!-- Chat Panel -->
    <Transition name="slide">
      <div
        v-if="showPanel"
        class="ai-panel"
        :class="{ maximized: isMaximized }"
        :style="panelStyle"
      >
        <!-- Resize handle (left edge) -->
        <div
          v-if="!isMaximized"
          class="ai-resize-handle-left"
          @mousedown.prevent="startResizeWidth"
        />
        <!-- Resize handle (top edge) -->
        <div
          v-if="!isMaximized"
          class="ai-resize-handle-top"
          @mousedown.prevent="startResizeHeight"
        />
        <!-- Resize grip (top-left corner) -->
        <div
          v-if="!isMaximized"
          class="ai-resize-grip"
          @mousedown.prevent="startResizeCorner"
        >
          <svg width="10" height="10" viewBox="0 0 10 10">
            <line x1="0" y1="10" x2="10" y2="0" stroke="currentColor" stroke-width="1.2" />
            <line x1="0" y1="6" x2="6" y2="0" stroke="currentColor" stroke-width="1.2" />
            <line x1="0" y1="2" x2="2" y2="0" stroke="currentColor" stroke-width="1.2" />
          </svg>
        </div>

        <!-- Header -->
        <div class="ai-panel-header">
          <div class="ai-panel-title">
            <div class="ai-icon">✦</div>
            <span>AI Assistant</span>
          </div>
          <div class="flex items-center gap-1">
            <button class="ai-header-btn" @click="clearChat" title="New chat">
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="1 4 1 10 7 10" />
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
              </svg>
            </button>
            <button
              class="ai-header-btn"
              @click="isMaximized = !isMaximized"
              :title="isMaximized ? 'Restore' : 'Maximize'"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <template v-if="!isMaximized">
                  <polyline points="15 3 21 3 21 9" />
                  <polyline points="9 21 3 21 3 15" />
                  <line x1="21" y1="3" x2="14" y2="10" />
                  <line x1="3" y1="21" x2="10" y2="14" />
                </template>
                <template v-else>
                  <polyline points="4 14 10 14 10 20" />
                  <polyline points="20 10 14 10 14 4" />
                  <line x1="14" y1="10" x2="21" y2="3" />
                  <line x1="3" y1="21" x2="10" y2="14" />
                </template>
              </svg>
            </button>
            <button
              class="ai-header-btn"
              @click="showPanel = false"
              title="Close"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Messages -->
        <div ref="messagesContainer" class="ai-messages">
          <!-- Welcome -->
          <div v-if="messages.length === 0" class="ai-welcome">
            <div class="ai-welcome-icon">✦</div>
            <h3>How can I help?</h3>
            <p>
              Ask any question about the knowledge base. I'll find and cite
              relevant articles.
            </p>
          </div>

          <!-- Message list -->
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="ai-message"
            :class="msg.role"
          >
            <!-- User bubble -->
            <div v-if="msg.role === 'user'" class="ai-bubble user">
              {{ msg.content }}
            </div>

            <!-- Assistant bubble -->
            <template v-else>
              <div class="ai-bubble assistant" v-html="renderMarkdown(msg.content)" />

              <!-- Citations -->
              <div
                v-if="msg.citations && msg.citations.length"
                class="ai-citations"
              >
                <button
                  class="ai-sources-toggle"
                  @click="msg.showSources = !msg.showSources"
                >
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path
                      d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
                    />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  Source articles ({{ msg.citations.length }})
                  <svg
                    width="10"
                    height="10"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    :class="{ rotated: msg.showSources }"
                    class="chevron"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                <div v-if="msg.showSources" class="ai-sources-list">
                  <a
                    v-for="c in msg.citations"
                    :key="c.name"
                    class="ai-source-item"
                    :href="getArticleUrl(c)"
                    target="_blank"
                  >
                    <div class="ai-source-icon">
                      <svg
                        width="13"
                        height="13"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <path
                          d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
                        />
                        <polyline points="14 2 14 8 20 8" />
                      </svg>
                    </div>
                    <div>
                      <div class="ai-source-title">{{ c.title }}</div>
                      <div class="ai-source-meta">{{ c.category }}</div>
                    </div>
                  </a>
                </div>
              </div>

              <!-- Follow-up suggestions -->
              <div
                v-if="msg.suggestions && msg.suggestions.length && !msg.isTyping"
                class="ai-suggestions"
              >
                <button
                  v-for="s in msg.suggestions"
                  :key="s"
                  class="ai-suggestion-chip"
                  @click="askQuestion(s)"
                >
                  {{ s }}
                </button>
              </div>
            </template>
          </div>
        </div>

        <!-- Input -->
        <div class="ai-input-area">
          <textarea
            ref="inputEl"
            v-model="inputText"
            class="ai-input"
            placeholder="Ask about any article..."
            rows="1"
            @input="autoResize"
            @keydown.enter.exact.prevent="sendQuestion"
          />
          <button
            class="ai-send-btn"
            :disabled="!inputText.trim() || isLoading"
            @click="sendQuestion"
            title="Send"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.2"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, nextTick, reactive, computed } from "vue";
import { createResource } from "frappe-ui";

interface Citation {
  name: string;
  title: string;
  category: string;
  url?: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  suggestions?: string[];
  isTyping?: boolean;
  showSources?: boolean;
}

const showPanel = ref(false);
const inputText = ref("");
const isLoading = ref(false);
const messagesContainer = ref<HTMLElement | null>(null);
const inputEl = ref<HTMLTextAreaElement | null>(null);
const messages = reactive<Message[]>([]);

// ── Resize / Maximize state ──────────────────────────────────
const isMaximized = ref(false);
const panelWidth = ref(400);
const panelHeight = ref(600);

const panelStyle = computed(() => {
  if (isMaximized.value) return {};
  return {
    width: panelWidth.value + "px",
    height: panelHeight.value + "px",
  };
});

function startResizeWidth(e: MouseEvent) {
  const startX = e.clientX;
  const startW = panelWidth.value;
  const onMove = (ev: MouseEvent) => {
    const delta = startX - ev.clientX;
    panelWidth.value = Math.max(320, Math.min(startW + delta, window.innerWidth - 48));
  };
  const onUp = () => {
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
  };
  document.addEventListener("mousemove", onMove);
  document.addEventListener("mouseup", onUp);
}

function startResizeHeight(e: MouseEvent) {
  const startY = e.clientY;
  const startH = panelHeight.value;
  const onMove = (ev: MouseEvent) => {
    const delta = startY - ev.clientY;
    panelHeight.value = Math.max(300, Math.min(startH + delta, window.innerHeight - 48));
  };
  const onUp = () => {
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
  };
  document.addEventListener("mousemove", onMove);
  document.addEventListener("mouseup", onUp);
}

function startResizeCorner(e: MouseEvent) {
  const startX = e.clientX;
  const startY = e.clientY;
  const startW = panelWidth.value;
  const startH = panelHeight.value;
  const onMove = (ev: MouseEvent) => {
    panelWidth.value = Math.max(320, Math.min(startW + (startX - ev.clientX), window.innerWidth - 48));
    panelHeight.value = Math.max(300, Math.min(startH + (startY - ev.clientY), window.innerHeight - 48));
  };
  const onUp = () => {
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
  };
  document.addEventListener("mousemove", onMove);
  document.addEventListener("mouseup", onUp);
}

function renderMarkdown(text: string): string {
  if (!text) return "";
  // Simple markdown: bold, italic, code, lists, paragraphs
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  // Code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, "<pre><code>$2</code></pre>");
  // Inline code
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // Italic
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  // Unordered lists
  html = html.replace(/^[-*] (.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");
  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, "<li>$1</li>");
  // Markdown links [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="ai-inline-link">$1</a>');
  // Paragraphs
  html = html
    .split("\n\n")
    .map((p) => (p.startsWith("<") ? p : `<p>${p}</p>`))
    .join("");
  html = html.replace(/\n/g, "<br>");
  return html;
}

function getArticleUrl(citation: Citation): string {
  return citation.url || `/helpdesk/kb/articles/${citation.name}`;
}

function autoResize() {
  const el = inputEl.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 200) + "px";
}

function scrollToBottom() {
  nextTick(() => {
    const el = messagesContainer.value;
    if (el) el.scrollTop = el.scrollHeight;
  });
}

function clearChat() {
  messages.splice(0, messages.length);
}

function askQuestion(question: string) {
  inputText.value = question;
  sendQuestion();
}

async function sendQuestion() {
  const question = inputText.value.trim();
  if (!question || isLoading.value) return;

  inputText.value = "";
  if (inputEl.value) inputEl.value.style.height = "auto";

  // Add user message
  messages.push({ role: "user", content: question });

  // Add typing indicator
  messages.push({
    role: "assistant",
    content: "Thinking...",
    isTyping: true,
  });
  scrollToBottom();

  isLoading.value = true;

  // Build conversation history (exclude typing indicators)
  const history = messages
    .filter((m) => !m.isTyping)
    .slice(0, -1)
    .map((m) => ({ role: m.role, content: m.content }));

  try {
    const res = createResource({
      url: "helpdesk.api.ai_chat.ask",
      makeParams: () => ({
        question: question,
        conversation_history: JSON.stringify(history),
      }),
    });

    await res.fetch();

    // Remove typing indicator
    const typingIdx = messages.findIndex((m) => m.isTyping);
    if (typingIdx !== -1) messages.splice(typingIdx, 1);

    const data = res.data || {};
    const citations = data.cited_articles || [];
    messages.push({
      role: "assistant",
      content: data.answer || "No answer available.",
      citations: citations,
      suggestions: data.suggested_questions || [],
      showSources: citations.length > 0,
    });
  } catch (e: any) {
    const typingIdx = messages.findIndex((m) => m.isTyping);
    if (typingIdx !== -1) messages.splice(typingIdx, 1);

    messages.push({
      role: "assistant",
      content: "Sorry, I encountered an error. Please try again.",
    });
  }

  isLoading.value = false;
  scrollToBottom();
}
</script>

<style scoped>
/* ─── Toggle Button ─────────────────────────────────────────── */
.ai-chat-toggle {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #8b5cf6, #6366f1, #3b82f6);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
  transition: transform 0.2s, box-shadow 0.2s;
}
.ai-chat-toggle:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 28px rgba(99, 102, 241, 0.55);
}

/* ─── Panel ─────────────────────────────────────────────────── */
.ai-panel {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 10000;
  width: 400px;
  max-width: calc(100vw - 48px);
  height: 600px;
  max-height: calc(100vh - 48px);
  border-radius: 16px;
  border: 1px solid var(--gray-200, #e5e7eb);
  background: var(--bg-white, #ffffff);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.ai-panel.maximized {
  top: 24px;
  left: 24px;
  right: 24px;
  bottom: 24px;
  width: auto !important;
  height: auto !important;
  max-width: none;
  max-height: none;
  border-radius: 12px;
}

/* ─── Resize Handles ────────────────────────────────────────── */
.ai-resize-handle-left {
  position: absolute;
  top: 0;
  left: -3px;
  width: 6px;
  height: 100%;
  cursor: ew-resize;
  z-index: 10;
}
.ai-resize-handle-top {
  position: absolute;
  top: -3px;
  left: 0;
  width: 100%;
  height: 6px;
  cursor: ns-resize;
  z-index: 10;
}
.ai-resize-grip {
  position: absolute;
  top: -2px;
  left: -2px;
  width: 16px;
  height: 16px;
  cursor: nwse-resize;
  z-index: 11;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gray-400, #9ca3af);
  transform: rotate(90deg);
}
.ai-resize-grip:hover {
  color: var(--gray-600, #4b5563);
}

/* ─── Header ────────────────────────────────────────────────── */
.ai-panel-header {
  padding: 14px 16px;
  border-bottom: 1px solid var(--gray-200, #e5e7eb);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-surface, #f9fafb);
}

.ai-panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 14px;
  color: var(--gray-900, #111827);
}

.ai-icon {
  width: 30px;
  height: 30px;
  background: linear-gradient(135deg, #8b5cf6, #6366f1, #3b82f6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: white;
  box-shadow: 0 2px 10px rgba(99, 102, 241, 0.35);
}

.ai-header-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--gray-500, #6b7280);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s;
}
.ai-header-btn:hover {
  background: var(--gray-100, #f3f4f6);
  color: var(--gray-900, #111827);
}

/* ─── Messages ──────────────────────────────────────────────── */
.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.ai-messages::-webkit-scrollbar {
  width: 4px;
}
.ai-messages::-webkit-scrollbar-thumb {
  background: var(--gray-300, #d1d5db);
  border-radius: 4px;
}

/* ─── Welcome ───────────────────────────────────────────────── */
.ai-welcome {
  text-align: center;
  padding: 40px 20px;
  color: var(--gray-400, #9ca3af);
}
.ai-welcome-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #8b5cf6, #6366f1, #3b82f6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: white;
}
.ai-welcome h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-900, #111827);
  margin: 0 0 6px;
}
.ai-welcome p {
  font-size: 13px;
  margin: 0;
  line-height: 1.5;
}

/* ─── Message Bubbles ───────────────────────────────────────── */
.ai-message {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ai-message.user {
  align-items: flex-end;
}
.ai-message.assistant {
  align-items: flex-start;
}

.ai-bubble {
  max-width: 88%;
  padding: 10px 14px;
  font-size: 13.5px;
  line-height: 1.65;
  word-break: break-word;
  border-radius: 14px;
}

.ai-bubble.user {
  background: var(--blue-600, #4f46e5);
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-bubble.assistant {
  background: var(--gray-100, #f3f4f6);
  color: var(--gray-800, #1f2937);
  border-bottom-left-radius: 4px;
}

.ai-bubble.assistant :deep(p) {
  margin: 0 0 8px;
}
.ai-bubble.assistant :deep(p:last-child) {
  margin-bottom: 0;
}
.ai-bubble.assistant :deep(ul),
.ai-bubble.assistant :deep(ol) {
  margin: 6px 0;
  padding-left: 20px;
}
.ai-bubble.assistant :deep(li) {
  margin-bottom: 4px;
}
.ai-bubble.assistant :deep(strong) {
  font-weight: 600;
}
.ai-bubble.assistant :deep(code) {
  background: var(--gray-200, #e5e7eb);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 12px;
}
.ai-bubble.assistant :deep(pre) {
  background: var(--gray-200, #e5e7eb);
  padding: 10px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 12px;
}
.ai-bubble.assistant :deep(.ai-inline-link) {
  color: var(--blue-600, #2563eb);
  text-decoration: none;
  font-weight: 500;
}
.ai-bubble.assistant :deep(.ai-inline-link:hover) {
  text-decoration: underline;
}

/* ─── Citations ─────────────────────────────────────────────── */
.ai-citations {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 88%;
}

.ai-sources-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border: 1px solid var(--gray-200, #e5e7eb);
  border-radius: 20px;
  background: white;
  color: var(--gray-600, #4b5563);
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.15s;
}
.ai-sources-toggle:hover {
  background: var(--gray-50, #f9fafb);
  border-color: var(--gray-300, #d1d5db);
}
.chevron {
  transition: transform 0.2s;
}
.chevron.rotated {
  transform: rotate(180deg);
}

.ai-sources-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ai-source-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid var(--gray-200, #e5e7eb);
  border-radius: 10px;
  background: white;
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
  color: inherit;
}
.ai-source-item:hover {
  border-color: var(--blue-400, #60a5fa);
  background: var(--blue-50, #eff6ff);
}

.ai-source-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--blue-50, #eff6ff);
  color: var(--blue-500, #3b82f6);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ai-source-title {
  font-size: 12.5px;
  font-weight: 500;
  color: var(--gray-900, #111827);
}

.ai-source-meta {
  font-size: 11px;
  color: var(--gray-400, #9ca3af);
}

/* ─── Suggestions ───────────────────────────────────────────── */
.ai-suggestions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 88%;
}

.ai-suggestion-chip {
  background: white;
  border: 1px solid var(--gray-200, #e5e7eb);
  border-radius: 8px;
  color: var(--gray-600, #4b5563);
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
  padding: 6px 12px;
  text-align: left;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
  line-height: 1.4;
}
.ai-suggestion-chip:hover {
  background: var(--blue-50, #eff6ff);
  border-color: var(--blue-400, #60a5fa);
  color: var(--blue-600, #2563eb);
}

/* ─── Input ─────────────────────────────────────────────────── */
.ai-input-area {
  border-top: 1px solid var(--gray-200, #e5e7eb);
  padding: 12px 14px;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--bg-surface, #f9fafb);
}

.ai-input {
  flex: 1;
  background: white;
  border: 1px solid var(--gray-200, #e5e7eb);
  border-radius: 20px;
  padding: 9px 14px;
  color: var(--gray-900, #111827);
  font-family: inherit;
  font-size: 13.5px;
  outline: none;
  resize: none;
  min-height: 40px;
  max-height: 200px;
  line-height: 1.5;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.ai-input:focus {
  border-color: var(--blue-400, #60a5fa);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
.ai-input::placeholder {
  color: var(--gray-400, #9ca3af);
}

.ai-send-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: opacity 0.15s, transform 0.15s;
}
.ai-send-btn:hover:not(:disabled) {
  transform: scale(1.05);
}
.ai-send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ─── Transition ────────────────────────────────────────────── */
.slide-enter-active,
.slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
}
</style>

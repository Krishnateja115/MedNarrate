// Readable names for the AI provider ids stored in telemetry.
const LABELS: Record<string, string> = {
  dev_gemini: 'Google Gemini',
  gemini: 'Google Gemini',
  vertex_ai: 'Google Vertex AI',
  ollama: 'Ollama (local)',
  local: 'Local model (offline)',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  mistral: 'Mistral',
  groq: 'Groq (gpt-oss)',
  groq_qwen: 'Groq (Qwen)',
  cerebras: 'Cerebras',
  openrouter: 'OpenRouter',
  github: 'GitHub Models',
  fallback: 'Built-in safe fallback (no AI)',
};

export function providerLabel(id?: string | null): string {
  if (!id) return 'Unknown';
  const key = id.toLowerCase();
  if (LABELS[key]) return LABELS[key];
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function modelLabel(model?: string | null): string {
  return !model || model === 'unknown' ? '—' : model;
}

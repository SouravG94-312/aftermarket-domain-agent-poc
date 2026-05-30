import { BackendChatRequest, BackendChatResponse } from "../types/chat";

export async function sendChatMessage(
  payload: BackendChatRequest
): Promise<BackendChatResponse> {
  const response = await fetch("/api/v1/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    credentials: "include",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Chat API failed: ${response.status} ${text}`);
  }

  return response.json();
}
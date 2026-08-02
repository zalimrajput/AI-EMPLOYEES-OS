"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Bot, Paperclip, Send, Sparkles } from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { AIMessage } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { useSession } from "@/hooks/use-session";
import { sendMessage } from "@/services/data";

function TypingDots() {
  return (
    <div className="flex items-center gap-1.5 py-2">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 animate-typing rounded-full bg-primary-soft"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

/** Lightweight markdown-ish rendering for assistant replies. */
function MessageBody({ text }: { text: string }) {
  return (
    <div className="space-y-2 text-sm leading-relaxed">
      {text.split("\n").map((line, i) => {
        if (line.startsWith("**") && line.endsWith("**")) {
          return <p key={i} className="font-bold text-white">{line.replace(/\*\*/g, "")}</p>;
        }
        if (line.startsWith("- ") || line.startsWith("• ")) {
          return (
            <p key={i} className="flex gap-2 text-slate-200">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gradient-to-r from-primary to-accent" />
              <span>{line.slice(2)}</span>
            </p>
          );
        }
        if (!line.trim()) return <div key={i} className="h-2" />;
        return <p key={i} className="text-slate-200">{line}</p>;
      })}
    </div>
  );
}

const REPLIES = [
  "Done! I've drafted it and queued it for review. Want me to send it now?",
  "I found 3 related records in the CRM. Here's what I prepared — approve and I'll execute.",
  "Completed ✅ — updated the pipeline and scheduled the follow-up for Friday at 3 PM.",
  "Here's the summary you asked for. I also extracted 5 action items and created tasks for each.",
  "On it. I'll track this conversation and remind you if there's no reply within 3 days.",
];

export function ChatInterface({
  employeeName,
  conversationId,
  initialMessages,
}: {
  employeeName: string;
  conversationId: string;
  initialMessages: AIMessage[];
}) {
  const { data: session } = useSession();
  const [messages, setMessages] = useState<AIMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, thinking]);

  async function handleSend() {
    const text = input.trim();
    if (!text || thinking) return;
    setInput("");
    setThinking(true);

    const userMsg: AIMessage = {
      id: `local-${Date.now()}`,
      conversation_id: conversationId,
      role: "user",
      message: text,
    };
    setMessages((m) => [...m, userMsg]);

    // persist to supabase (best-effort)
    const isDemo = conversationId.startsWith("demo-");
    if (!isDemo) {
      await sendMessage(conversationId, "user", text).catch(() => null);
    }

    // simulate streaming reply
    const reply = REPLIES[Math.floor(Math.random() * REPLIES.length)];
    const streamed: AIMessage = {
      id: `local-${Date.now() + 1}`,
      conversation_id: conversationId,
      role: "assistant",
      message: "",
    };
    setMessages((m) => [...m, streamed]);

    const chars = reply.split("");
    for (let i = 0; i < chars.length; i++) {
      await new Promise((r) => setTimeout(r, 14));
      setMessages((m) =>
        m.map((msg) => (msg.id === streamed.id ? { ...msg, message: reply.slice(0, i + 1) } : msg))
      );
    }
    if (!isDemo) {
      await sendMessage(conversationId, "assistant", reply).catch(() => null);
    }
    setThinking(false);
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto p-4 md:p-6 no-scrollbar">
        {messages.map((msg) => {
          const isUser = msg.role === "user";
          return (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className={cn("flex gap-3", isUser && "flex-row-reverse")}
            >
              {isUser ? (
                <Avatar name={session?.user?.name ?? session?.user?.email} size="sm" className="shrink-0" />
              ) : (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary to-secondary">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              )}
              <div
                className={cn(
                  "max-w-[78%] rounded-2xl border px-4 py-3 shadow-lg",
                  isUser
                    ? "border-transparent bg-gradient-to-r from-primary to-secondary text-white"
                    : "border-border-soft bg-card-soft/70"
                )}
              >
                {!isUser && (
                  <p className="mb-1.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-primary-soft">
                    <Sparkles className="h-3 w-3" /> {employeeName}
                  </p>
                )}
                {msg.message ? <MessageBody text={msg.message} /> : <TypingDots />}
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="border-t border-border-soft bg-card/40 p-3 md:p-4">
        <div className="relative">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={`Message ${employeeName}…`}
            className="min-h-[56px] max-h-36 resize-none pr-20 py-3.5"
          />
          <div className="absolute bottom-2.5 right-2.5 flex items-center gap-1.5">
            <Button variant="ghost" size="iconSm" aria-label="Attach">
              <Paperclip className="h-4 w-4" />
            </Button>
            <Button size="iconSm" onClick={handleSend} disabled={!input.trim() || thinking} aria-label="Send">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <p className="mt-2 text-center text-[11px] text-slate-600">
          AI Employee OS can make mistakes. Review important actions before they execute.
        </p>
      </div>
    </div>
  );
}

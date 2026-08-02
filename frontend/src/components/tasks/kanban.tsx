"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { CalendarClock, Plus } from "lucide-react";
import type { Task, TaskStatus } from "@/lib/api/types";
import { STATUS_LABELS, TASK_STATUSES, PRIORITY_COLORS } from "@/services/data";
import { Badge } from "@/components/ui/badge";
import { cn, timeAgo } from "@/lib/utils";

const COLUMN_COLORS: Record<TaskStatus, string> = {
  todo: "from-slate-500 to-slate-400",
  in_progress: "from-primary to-secondary",
  review: "from-warning to-accent",
  done: "from-success to-accent",
};

export function KanbanBoard({
  tasks,
  onMove,
}: {
  tasks: Task[];
  onMove?: (id: string, status: TaskStatus) => void;
}) {
  const [dragOver, setDragOver] = useState<TaskStatus | null>(null);

  const columns = TASK_STATUSES.map((status) => ({
    status,
    items: tasks.filter((t) => (t.status ?? "todo") === status),
  }));

  function handleDrop(status: TaskStatus, taskId: string) {
    onMove?.(taskId, status);
    setDragOver(null);
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      {columns.map(({ status, items }) => (
        <div
          key={status}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(status);
          }}
          onDragLeave={() => setDragOver((s) => (s === status ? null : s))}
          onDrop={(e) => {
            const id = e.dataTransfer.getData("taskId");
            if (id) handleDrop(status, id);
          }}
          className={cn(
            "flex flex-col gap-3 rounded-2xl border p-3 transition-all duration-200",
            dragOver === status ? "border-primary/60 bg-primary/5" : "border-border-soft bg-card-soft/30"
          )}
        >
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <span className={cn("h-2 w-2 rounded-full bg-gradient-to-r", COLUMN_COLORS[status])} />
              <span className="text-sm font-bold text-white">{STATUS_LABELS[status]}</span>
              <span className="rounded-full bg-card px-1.5 py-0.5 text-[10px] font-bold text-slate-400">{items.length}</span>
            </div>
            <Plus className="h-3.5 w-3.5 text-slate-600" />
          </div>

          <div className="space-y-2.5">
            {items.map((task) => (
              <motion.div
                key={task.id}
                layout
                draggable
                onDragStartCapture={(e) => {
                  e.dataTransfer.setData("taskId", task.id);
                  e.dataTransfer.effectAllowed = "move";
                }}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{ y: -3 }}
                className="group cursor-grab rounded-xl border border-border-soft bg-card p-3.5 shadow-lg shadow-black/20 transition-colors hover:border-primary/40 active:cursor-grabbing"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold leading-snug text-slate-100">{task.title}</p>
                  <span
                    className="mt-1 h-2 w-2 shrink-0 rounded-full"
                    style={{ backgroundColor: PRIORITY_COLORS[task.priority ?? "medium"] }}
                  />
                </div>
                {task.description && (
                  <p className="mt-1.5 line-clamp-2 text-xs text-slate-500">{task.description}</p>
                )}
                <div className="mt-3 flex items-center justify-between">
                  <Badge variant={task.priority === "high" || task.priority === "urgent" ? "danger" : "secondary"} className="text-[10px] capitalize">
                    {task.priority ?? "medium"}
                  </Badge>
                  <span className="inline-flex items-center gap-1 text-[11px] text-slate-500">
                    <CalendarClock className="h-3 w-3" />
                    {timeAgo(task.due_date ?? task.created_at)}
                  </span>
                </div>
                {task.ai_created && (
                  <p className="mt-2 inline-flex items-center gap-1 rounded-md bg-primary/10 px-1.5 py-0.5 text-[10px] font-bold text-primary-soft">
                    🤖 AI-created
                  </p>
                )}
              </motion.div>
            ))}
            {items.length === 0 && (
              <div className="rounded-xl border border-dashed border-border-soft p-6 text-center text-xs text-slate-600">
                Drop tasks here
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

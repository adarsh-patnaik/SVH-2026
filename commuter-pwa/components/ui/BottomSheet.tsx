"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

interface BottomSheetProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

/**
 * A lightweight bottom sheet: CSS transform + touch handlers give a
 * draggable feel without pulling in a gesture library. Dragging past
 * ~90px or with enough velocity dismisses the sheet; otherwise it
 * springs back via a CSS transition.
 */
export function BottomSheet({ open, onClose, title, children }: BottomSheetProps) {
  const [dragY, setDragY] = useState(0);
  const [dragging, setDragging] = useState(false);
  const startY = useRef<number | null>(null);
  const sheetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (open) document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const handleTouchStart = (e: React.TouchEvent) => {
    startY.current = e.touches[0].clientY;
    setDragging(true);
  };
  const handleTouchMove = (e: React.TouchEvent) => {
    if (startY.current === null) return;
    const delta = e.touches[0].clientY - startY.current;
    setDragY(Math.max(0, delta));
  };
  const handleTouchEnd = () => {
    setDragging(false);
    if (dragY > 90) {
      onClose();
    } else {
      setDragY(0);
    }
    startY.current = null;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center md:items-center">
      <button
        aria-label="Close"
        onClick={onClose}
        className="absolute inset-0 bg-black/30 backdrop-blur-[1px]"
        style={{ opacity: dragging ? Math.max(0.15, 1 - dragY / 300) : 1 }}
      />
      <div
        ref={sheetRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="relative z-10 w-full max-w-md rounded-t-3xl border border-border bg-surface-elevated shadow-[var(--shadow-elevated)] md:rounded-3xl"
        style={{
          transform: `translateY(${dragY}px)`,
          transition: dragging ? "none" : "transform 320ms cubic-bezier(0.32, 0.72, 0, 1)",
          animation: dragging ? "none" : "sheet-up 320ms cubic-bezier(0.32, 0.72, 0, 1)",
        }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <div className="flex justify-center pt-2.5 md:hidden">
          <div className="h-1.5 w-10 rounded-full bg-border" />
        </div>
        <div className="max-h-[75vh] overflow-y-auto overscroll-contain px-5 pb-6 pt-3">
          {children}
        </div>
      </div>
    </div>
  );
}

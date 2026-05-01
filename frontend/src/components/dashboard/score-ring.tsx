"use client";

import { motion } from "motion/react";

interface ScoreRingProps {
  score: number;
  label: string;
}

export function ScoreRing({ score, label }: ScoreRingProps) {
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 85 ? "#22c55e" : score >= 65 ? "#fbbf24" : "#fb7185";

  return (
    <div className="relative flex h-44 w-44 items-center justify-center">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 180 180">
        <circle cx="90" cy="90" r={radius} stroke="rgba(255,255,255,.08)" strokeWidth="12" fill="none" />
        <motion.circle
          cx="90"
          cy="90"
          r={radius}
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.1, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute text-center">
        <motion.div
          className="text-4xl font-black tracking-tight text-white"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          {score}
        </motion.div>
        <div className="mt-1 text-sm font-medium text-slate-400">{label}</div>
      </div>
    </div>
  );
}

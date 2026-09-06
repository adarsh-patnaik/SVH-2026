"use client";

import dynamic from "next/dynamic";
import { MapSkeleton } from "@/components/ui/Skeleton";
import type { ComponentProps } from "react";
import type { LiveMap as LiveMapType } from "./LiveMap";

export const LiveMapLoader = dynamic<ComponentProps<typeof LiveMapType>>(
  () => import("./LiveMap").then((mod) => mod.LiveMap),
  {
    ssr: false,
    loading: () => <MapSkeleton />,
  }
);

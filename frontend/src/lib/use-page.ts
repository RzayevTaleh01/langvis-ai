"use client";
import { useEffect } from "react";
import { useLive, type Page } from "@/components/live-provider";

// Each page says where the learner is: the header lights its tab, and a
// lesson started on another page stops.
export function usePage(page: Page) {
  const { setPage } = useLive();
  useEffect(() => { setPage(page); }, [page, setPage]);
}

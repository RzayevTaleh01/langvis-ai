"use client";
// The Tutor: free conversation on the board, any topic, any question.
import { Classroom } from "@/components/classroom";
import { usePage } from "@/lib/use-page";

export default function TutorPage() {
  usePage("tutor");
  return <Classroom kind="tutor" />;
}

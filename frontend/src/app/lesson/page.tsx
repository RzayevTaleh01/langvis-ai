"use client";
// A course lesson: the board, with the course syllabus on the left.
import { Classroom } from "@/components/classroom";
import { usePage } from "@/lib/use-page";

export default function LessonPage() {
  usePage("lesson");
  return <Classroom kind="lesson" />;
}

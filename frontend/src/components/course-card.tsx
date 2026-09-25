"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
// One course as a simple catalog card, without a picture: the language and
// its levels, the title, who it is for, its size, and one action.

export function CourseCard({ course, current, action, onClick, disabled }: {
  course: any;
  current?: boolean;
  action?: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
}) {
  const weeks: any[] = Array.isArray(course.weeks) ? course.weeks : [];
  // "English · A2 → B1 · Sentence builder" -> "Sentence builder"; a title with
  // only the name, levels and length gets a plain one.
  const named = String(course.title || "").split(" · ")
    .filter((p) => p !== course.name && p !== course.levels && !/^\d+ weeks?$/.test(p));
  const title = named.pop() || `Speak ${course.name} step by step`;
  const body = (
    <>
      <div className="cc-head">
        <span className="cc-lang">{course.name}</span>
        <span className="badge lvl">{course.levels}</span>
        {current && <span className="cc-flag">Your course</span>}
      </div>
      <h3 className="cc-title">{title}</h3>
      {course.learner && <p className="cc-learner">{course.learner}</p>}
      <div className="cc-meta">{`${course.lessons} lessons · ${weeks.length || course.weeks} weeks`}</div>
      {action && <div className="cc-foot">{action}</div>}
    </>
  );
  return onClick
    ? <button type="button" className={"cc" + (current ? " current" : "")} onClick={onClick} disabled={disabled}>{body}</button>
    : <article className={"cc" + (current ? " current" : "")}>{body}</article>;
}

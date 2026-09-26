// Every icon of the app, from lucide-react. The names stay the app's own, so a
// page asks for "the Tutor icon", not for a drawing.

import {
  BookOpen, ClipboardCheck, Globe, House, Keyboard, MessageSquare, MessagesSquare, Mic, MicOff,
  Play, RotateCcw, SendHorizontal, Settings, SkipForward, Square, Trash2, UserRound,
  type LucideIcon,
} from "lucide-react";

type P = { className?: string };

const icon = (Icon: LucideIcon, fallback?: string, fill = false) => {
  const Named = ({ className = fallback }: P) => (
    <Icon className={className} aria-hidden="true" {...(fill ? { fill: "currentColor" } : {})} />
  );
  Named.displayName = Icon.displayName;
  return Named;
};

export const GlobeIcon = icon(Globe, "chip-icon size-4");
export const TopicIcon = icon(MessageSquare, "topic-icon size-4");
export const GrammarIcon = icon(ClipboardCheck, "topic-icon size-4");
export const HomeIcon = icon(House, "nav-icon");
export const BookIcon = icon(BookOpen, "nav-icon");
export const ChatIcon = icon(MessagesSquare, "nav-icon");
export const UserIcon = icon(UserRound, "nav-icon");
export const GearIcon = icon(Settings);
export const RestartIcon = icon(RotateCcw);
export const PlayIcon = icon(Play, undefined, true);
export const SkipIcon = icon(SkipForward);
export const MicOnIcon = icon(Mic, "mic-on");
export const MicOffIcon = icon(MicOff, "mic-off");
export const SendIcon = icon(SendHorizontal);
export const KeyboardIcon = icon(Keyboard);
export const StopIcon = icon(Square, undefined, true);
export const TrashIcon = icon(Trash2);

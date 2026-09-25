// The hand-drawn icons of the original page, as they were.

type P = { className?: string };

export const GlobeIcon = ({ className = "chip-icon" }: P) => (
  <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
    <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="2" />
    <path d="M3 12h18M12 3c3 3.2 3 14.8 0 18M12 3c-3 3.2-3 14.8 0 18" fill="none" stroke="currentColor" strokeWidth="1.8" />
  </svg>
);

export const TopicIcon = ({ className = "topic-icon" }: P) => (
  <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
    <path d="M4 5h16v11H8l-4 4z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
  </svg>
);

export const GrammarIcon = ({ className = "topic-icon" }: P) => (
  <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
    <path d="M5 4h11l3 3v13H5z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    <path d="M8.5 12l2.2 2.2L15.5 9.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const HomeIcon = ({ className = "nav-icon" }: P) => (
  <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
    <path d="M3 11l9-7 9 7" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M5 10v10h14V10" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    <path d="M10 20v-6h4v6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
  </svg>
);

export const BookIcon = ({ className = "nav-icon" }: P) => (
  <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
    <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    <path d="M4 20.5A2.5 2.5 0 0 0 6.5 23H20v-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    <path d="M9 8h7M9 12h5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

export const ChatIcon = ({ className = "nav-icon" }: P) => (
  <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
    <path d="M4 5h16v11H9l-5 4z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    <path d="M8 9.5h8M8 12.5h5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

export const UserIcon = ({ className = "nav-icon" }: P) => (
  <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
    <circle cx="12" cy="8" r="4" fill="none" stroke="currentColor" strokeWidth="1.8" />
    <path d="M4 21c0-4 3.6-7 8-7s8 3 8 7" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

export const GearIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" d="M10.3 2.6h3.4l.5 2.6c.6.2 1.2.5 1.7.9l2.5-.9 1.7 2.9-2 1.8c.1.6.1 1.3 0 1.9l2 1.8-1.7 2.9-2.5-.9c-.5.4-1.1.7-1.7.9l-.5 2.6h-3.4l-.5-2.6c-.6-.2-1.2-.5-1.7-.9l-2.5.9-1.7-2.9 2-1.8a6 6 0 0 1 0-1.9l-2-1.8 1.7-2.9 2.5.9c.5-.4 1.1-.7 1.7-.9z" />
    <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.8" />
  </svg>
);

export const RestartIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M4 12a8 8 0 1 0 2.4-5.7M4 4v4.5h4.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const PlayIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z" fill="currentColor" /></svg>
);

export const SkipIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M5 5l9 7-9 7zM17 5v14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
  </svg>
);

export const MicOnIcon = () => (
  <svg className="mic-on" viewBox="0 0 24 24" aria-hidden="true">
    <rect x="9" y="3" width="6" height="11" rx="3" fill="currentColor" />
    <path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export const MicOffIcon = () => (
  <svg className="mic-off" viewBox="0 0 24 24" aria-hidden="true">
    <path d="M15 10.5V6a3 3 0 0 0-5.6-1.5M9 9v2a3 3 0 0 0 4.7 2.5M5.5 11a6.5 6.5 0 0 0 10.4 5.2M18.5 11c0 .8-.1 1.5-.4 2.2M12 17.5V21M4 4l16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export const SendIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12l16-8-6 16-2.5-6.5z" fill="currentColor" /></svg>
);

export const KeyboardIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <rect x="2.5" y="6" width="19" height="12" rx="2.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
    <path d="M6 10h.01M9.5 10h.01M13 10h.01M16.5 10h.01M6 13.5h.01M18 13.5h.01M9 14h6" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
  </svg>
);

export const StopIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" /></svg>
);

export const TrashIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M5 7h14M10 7V5h4v2M7 7l1 12h8l1-12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

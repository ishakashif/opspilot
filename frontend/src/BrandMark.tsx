export default function BrandMark({ size = 32 }: { size?: number }) {
  return (
    <svg
      className="brand-mark-svg"
      width={size}
      height={size}
      viewBox="0 0 32 32"
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="9" fill="#121722" />
      <rect
        x="0.6"
        y="0.6"
        width="30.8"
        height="30.8"
        rx="8.4"
        fill="none"
        stroke="#8ea2ff"
        strokeOpacity="0.45"
      />
      <path
        d="M8 21.6c2.35-5.1 4.7-7.9 8-7.9s5.65 2.8 8 7.9"
        fill="none"
        stroke="#9eb0ff"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
      <circle cx="16" cy="18.1" r="2.05" fill="#d9d4ff" />
    </svg>
  )
}

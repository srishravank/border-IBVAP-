/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forensic: {
          bg: "#F4F1E8",
          surface: "#ECE9E0",
          elevated: "#FFFFFF",
          text: "#171717",
          muted: "#5E5E5E",
          subtle: "#8A877E",
          border: "#D6D2C8",
          borderDark: "#B8B3A7",
          graphite: "#292929",
          darkBg: "#111215",
          darkSurface: "#181A1F",
          darkBorder: "#272A30",
        },
        signal: {
          safe: "#C7FF3D",
          safeDark: "#1B3B12",
          warning: "#F5A623",
          warningDark: "#3D2B0F",
          threat: "#FF4D4D",
          threatDark: "#3E1212",
        },
        borderBg: "#F4F1E8",
        panelBg: "#ECE9E0",
        cardBg: "#FFFFFF",
        cardBorder: "#D6D2C8",
        accentCyan: "#171717",
        accentEmerald: "#171717",
        accentAmber: "#F5A623",
        accentRose: "#FF4D4D",
      },
      fontFamily: {
        mono: ['"IBM Plex Mono"', '"JetBrains Mono"', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['"Inter"', '"Manrope"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        sm: "3px",
        DEFAULT: "4px",
        md: "4px",
        lg: "6px",
        xl: "6px",
        "2xl": "8px",
      }
    },
  },
  plugins: [],
}

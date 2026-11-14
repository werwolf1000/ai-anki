/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#07070d", 900: "#0c0c16", 850: "#10101c", 800: "#141421", 700: "#1c1c2c", 600: "#262639", 500: "#34344a" },
      },
      fontFamily: {
        sans: ["Inter", '"Segoe UI Variable Text"', '"Segoe UI"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', '"Cascadia Code"', "Consolas", "monospace"],
      },
      boxShadow: {
        glow: "0 0 24px -4px rgba(244, 63, 94, 0.55)",
        "glow-violet": "0 0 32px -8px rgba(139, 92, 246, 0.65)",
        card: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 20px 40px -24px rgba(0,0,0,0.8)",
      },
    },
  },
  plugins: [],
};

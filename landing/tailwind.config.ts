import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gold: {
          DEFAULT: "#C5A059",
          muted: "#9E804B",
          dark: "#6B5530",
        },
        surface: {
          DEFAULT: "#111111",
          deep: "#0A0A0A",
          subtle: "#161616",
        },
        border: "#2A2A2A",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;

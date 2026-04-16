import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        maple: {
          yellow:   "#FFD700",
          orange:   "#FF8C00",
          dark:     "#0D0D1A",
          panel:    "#16162A",
          border:   "#2A2A4A",
          text:     "#E0E0F0",
          muted:    "#8888AA",
          green:    "#4ADE80",
          red:      "#F87171",
        },
      },
      fontFamily: {
        sans: ["Noto Sans KR", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;

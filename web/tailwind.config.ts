import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#080a0f",
        panel: "#0e121b",
        edge: "#1b2331",
        up: "#16c784",
        down: "#ea3943",
        amber: "#f0b90b",
        muted: "#7c8798",
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;

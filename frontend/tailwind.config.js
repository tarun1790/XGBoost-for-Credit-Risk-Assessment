/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: "#0b0f19",
          panel: "#161d30",
          card: "#1e2942",
          accent: "#3b82f6",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
        }
      },
      fontFamily: {
        sans: ["Outfit", "Inter", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(59, 130, 246, 0.15)",
        "glow-emerald": "0 0 20px rgba(16, 185, 129, 0.25)",
        "glow-rose": "0 0 20px rgba(244, 63, 94, 0.25)",
      }
    },
  },
  plugins: [],
}

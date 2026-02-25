/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        tide: {
          50: "#effbff",
          100: "#d9f4ff",
          200: "#b7e9ff",
          300: "#82d8ff",
          400: "#44bdf0",
          500: "#249fd6",
          600: "#197faf",
          700: "#186589",
          800: "#1a536f",
          900: "#1a465d",
          950: "#112d3d"
        },
        reef: {
          50: "#e8fff8",
          100: "#c8ffec",
          200: "#95ffda",
          300: "#52f7c2",
          400: "#1de0ab",
          500: "#06c291",
          600: "#029d76",
          700: "#037d60",
          800: "#07644d",
          900: "#0a5140",
          950: "#022f26"
        },
        ink: {
          50: "#f4f7fb",
          100: "#e8eef6",
          200: "#cedceb",
          300: "#a6bfd6",
          400: "#789fbe",
          500: "#5b83a7",
          600: "#476886",
          700: "#3a546d",
          800: "#33485c",
          900: "#1f2c3a",
          950: "#0f1724"
        }
      },
      fontFamily: {
        display: ["Sora", "Manrope", "Segoe UI", "sans-serif"],
        body: ["Manrope", "Segoe UI", "sans-serif"]
      },
      boxShadow: {
        glow: "0 22px 56px -28px rgba(3, 39, 64, 0.55)",
        smooth: "0 4px 16px rgba(20, 95, 122, 0.1)"
      },
      animation: {
        slideInUp: "slideInUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)",
        floatBubble: "floatBubble 8s ease-in-out infinite",
        ringPulse: "ringPulse 2.1s cubic-bezier(0.34, 0, 0.66, 1) infinite",
        orbFloat: "orbFloat 1.4s cubic-bezier(0.42, 0, 0.58, 1) infinite",
        beamScan: "beamScan 1.2s cubic-bezier(0.42, 0, 0.58, 1) infinite",
        dotBeat: "dotBeat 1.1s cubic-bezier(0.42, 0, 0.58, 1) infinite",
        letterSpin: "letterSpin 1.9s linear infinite"
      },
      keyframes: {
        slideInUp: {
          "0%": {
            opacity: "0",
            transform: "translateY(20px)"
          },
          "100%": {
            opacity: "1",
            transform: "translateY(0)"
          }
        },
        floatBubble: {
          "0%": {
            transform: "translateY(0) translateX(0)"
          },
          "25%": {
            transform: "translateY(-10px) translateX(5px)"
          },
          "50%": {
            transform: "translateY(-20px) translateX(-5px)"
          },
          "75%": {
            transform: "translateY(-10px) translateX(5px)"
          },
          "100%": {
            transform: "translateY(0) translateX(0)"
          }
        },
        ringPulse: {
          "0%": {
            opacity: "0.8",
            transform: "translate(-50%, -50%) scale(0.8)"
          },
          "50%": {
            opacity: "0.4"
          },
          "100%": {
            opacity: "0",
            transform: "translate(-50%, -50%) scale(1.45)"
          }
        },
        orbFloat: {
          "0%, 100%": {
            transform: "translate(-50%, -50%) translateY(-3px)"
          },
          "25%": {
            transform: "translate(-50%, -50%) translateY(1px)"
          },
          "50%": {
            transform: "translate(-50%, -50%) translateY(3px)"
          },
          "75%": {
            transform: "translate(-50%, -50%) translateY(0px)"
          }
        },
        beamScan: {
          "0%": {
            transform: "translateX(-110%)"
          },
          "100%": {
            transform: "translateX(270%)"
          }
        },
        dotBeat: {
          "0%, 100%": {
            opacity: "0.25",
            transform: "translateY(0) scale(1)"
          },
          "50%": {
            opacity: "0.95",
            transform: "translateY(-4px) scale(1.1)"
          }
        },
        letterSpin: {
          "0%": {
            transform: "rotate(0deg)"
          },
          "50%": {
            transform: "rotate(180deg)"
          },
          "100%": {
            transform: "rotate(360deg)"
          }
        }
      },
      transitionTimingFunction: {
        smooth: "cubic-bezier(0.34, 1.56, 0.64, 1)"
      },
      transitionDuration: {
        smooth: "300ms"
      }
    }
  },
  plugins: []
};

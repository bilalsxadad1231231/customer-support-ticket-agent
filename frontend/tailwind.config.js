/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1e293b',    // Deep Navy
        secondary: '#64748b',  // Slate Gray
        accent: '#3b82f6',    // Bright Blue
        success: '#10b981',   // Emerald Green
        warning: '#f59e0b',   // Amber
        error: '#ef4444',     // Red
        background: '#f8fafc', // Light Gray
      },
      fontFamily: {
        sans: ['Inter', 'Poppins', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
} 
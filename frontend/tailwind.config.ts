import type { Config } from "tailwindcss";
export default { content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"], theme: { extend: { colors: { paper: "#f5f1e8", ink: "#17211e", moss: "#456052", clay: "#a8563c", sand: "#ded4c2" }, fontFamily: { display: ["var(--font-serif)"], sans: ["var(--font-sans)"] } } }, plugins: [] } satisfies Config;

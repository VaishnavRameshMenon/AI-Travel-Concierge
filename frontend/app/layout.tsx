import type { Metadata } from "next";
import { DM_Sans, Playfair_Display } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
const sans=DM_Sans({subsets:["latin"],variable:"--font-sans"}); const serif=Playfair_Display({subsets:["latin"],variable:"--font-serif"});
export const metadata: Metadata={title:"TripPilot — travel, considered",description:"A thoughtful AI travel concierge."};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body className={`${sans.variable} ${serif.variable}`}><Providers>{children}</Providers></body></html>}

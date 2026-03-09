"use client";

import { SignIn, useAuth } from "@clerk/nextjs";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import HGBWordmark from "@/components/HGBWordmark";

export default function GatePage() {
  const { isSignedIn, isLoaded } = useAuth();
  const router = useRouter();

  // If already signed in, go straight to dashboard
  useEffect(() => {
    if (isLoaded && isSignedIn) {
      router.push("/dashboard");
    }
  }, [isLoaded, isSignedIn, router]);

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center px-4"
      style={{ backgroundColor: "#0A0A0A" }}
    >
      {/* Subtle top border accent */}
      <div
        className="fixed top-0 left-0 right-0 h-px"
        style={{ background: "linear-gradient(90deg, transparent, #C5A059, transparent)" }}
      />

      <div className="w-full max-w-sm">
        <HGBWordmark />

        <p
          className="text-center text-sm mb-8 tracking-wide"
          style={{ color: "#9E804B" }}
        >
          Partner Portal · Private Access
        </p>

        {/* Clerk SignIn component — styled to match HGB brand */}
        <SignIn
          routing="hash"
          afterSignInUrl="/dashboard"
          appearance={{
            variables: {
              colorPrimary: "#C5A059",
              colorBackground: "#111111",
              colorText: "#F5F5F5",
              colorTextSecondary: "#9E804B",
              colorInputBackground: "#0A0A0A",
              colorInputText: "#F5F5F5",
              colorNeutral: "#2A2A2A",
              fontFamily: "Inter, sans-serif",
              borderRadius: "6px",
            },
            elements: {
              card: {
                background: "#111111",
                border: "1px solid #2A2A2A",
                boxShadow: "0 0 40px rgba(197, 160, 89, 0.06)",
              },
              headerTitle: { color: "#F5F5F5", fontWeight: "600" },
              headerSubtitle: { color: "#9E804B" },
              socialButtonsBlockButton: {
                background: "#161616",
                border: "1px solid #2A2A2A",
                color: "#F5F5F5",
              },
              dividerLine: { background: "#2A2A2A" },
              dividerText: { color: "#9E804B" },
              formFieldLabel: { color: "#9E804B" },
              formFieldInput: {
                background: "#0A0A0A",
                border: "1px solid #2A2A2A",
                color: "#F5F5F5",
              },
              formButtonPrimary: {
                background: "#C5A059",
                color: "#0A0A0A",
                fontWeight: "600",
              },
              footerActionLink: { color: "#C5A059" },
              identityPreviewText: { color: "#F5F5F5" },
              identityPreviewEditButtonIcon: { color: "#9E804B" },
            },
          }}
        />
      </div>

      {/* Footer */}
      <p
        className="fixed bottom-6 text-xs"
        style={{ color: "#3A3A3A" }}
      >
        HGB Capital Management · Confidential
      </p>
    </main>
  );
}

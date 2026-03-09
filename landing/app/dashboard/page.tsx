"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import HGBWordmark from "@/components/HGBWordmark";

const STREAMLIT_URL = "http://localhost:8501";

export default function DashboardPage() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [status, setStatus] = useState<"loading" | "redirecting" | "error">("loading");

  useEffect(() => {
    if (!isLoaded) return;

    if (!isSignedIn) {
      window.location.href = "/";
      return;
    }

    async function launchDashboard() {
      try {
        // Get a short-lived Clerk session JWT
        const token = await getToken();
        if (!token) throw new Error("No token returned");

        setStatus("redirecting");

        // Small delay so user sees the "Launching…" message
        await new Promise((r) => setTimeout(r, 800));

        window.location.href = `${STREAMLIT_URL}?clerk_token=${encodeURIComponent(token)}`;
      } catch {
        setStatus("error");
      }
    }

    launchDashboard();
  }, [isLoaded, isSignedIn, getToken]);

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center px-4"
      style={{ backgroundColor: "#0A0A0A" }}
    >
      <div
        className="fixed top-0 left-0 right-0 h-px"
        style={{ background: "linear-gradient(90deg, transparent, #C5A059, transparent)" }}
      />

      <div className="w-full max-w-sm text-center">
        <HGBWordmark />

        {status === "loading" && (
          <>
            <Spinner />
            <p className="text-sm mt-4" style={{ color: "#9E804B" }}>
              Authenticating…
            </p>
          </>
        )}

        {status === "redirecting" && (
          <>
            <Spinner />
            <p className="text-sm mt-4" style={{ color: "#C5A059" }}>
              Launching dashboard…
            </p>
            <p className="text-xs mt-2" style={{ color: "#3A3A3A" }}>
              Opening localhost:8501
            </p>
          </>
        )}

        {status === "error" && (
          <div
            className="mt-4 p-4 rounded-md text-sm"
            style={{ background: "#1A0A0A", border: "1px solid #4A1A1A", color: "#F87171" }}
          >
            <p className="font-medium mb-2">Could not launch dashboard</p>
            <p style={{ color: "#9E804B" }} className="text-xs mb-4">
              Make sure Streamlit is running on localhost:8501, then try again.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="text-xs px-4 py-2 rounded"
              style={{ background: "#C5A059", color: "#0A0A0A", fontWeight: 600 }}
            >
              Retry
            </button>
          </div>
        )}
      </div>
    </main>
  );
}

function Spinner() {
  return (
    <div className="flex justify-center mt-2">
      <div
        className="w-6 h-6 rounded-full border-2 border-t-transparent animate-spin"
        style={{ borderColor: "#C5A059", borderTopColor: "transparent" }}
      />
    </div>
  );
}

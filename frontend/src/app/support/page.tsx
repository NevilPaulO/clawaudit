import Link from "next/link";
import Script from "next/script";
import type React from "react";
import { ArrowLeft, ShieldCheck, Sparkles, Star } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const paypalContainerId = "paypal-container-WFK2UQN9QTC5G";
const paypalHostedButtonId = "WFK2UQN9QTC5G";

export default function SupportPage() {
  return (
    <main className="glass-grid relative min-h-screen overflow-hidden px-4 py-5 text-slate-100 lg:px-8">
      <Script
        id="paypal-hosted-buttons-sdk"
        src="https://www.paypal.com/sdk/js?client-id=BAA96Xd6x_Vx0DZPbLjPBdklAx-4eT54Bn55elf1FpfcBM1TqwoRf-ImwdYO0HDC3HVFyKK6b0O5RrN1Jo&components=hosted-buttons&disable-funding=venmo&currency=USD"
        strategy="afterInteractive"
      />
      <Script id="paypal-hosted-button-render" strategy="afterInteractive">
        {`
          (function renderClawAuditPayPalButton() {
            var attempts = 0;
            var timer = window.setInterval(function () {
              attempts += 1;
              var container = document.getElementById("${paypalContainerId}");
              if (!container || container.dataset.rendered === "true") {
                window.clearInterval(timer);
                return;
              }
              if (window.paypal && window.paypal.HostedButtons) {
                container.dataset.rendered = "true";
                window.paypal.HostedButtons({
                  hostedButtonId: "${paypalHostedButtonId}",
                }).render("#${paypalContainerId}");
                window.clearInterval(timer);
              }
              if (attempts > 80) {
                window.clearInterval(timer);
              }
            }, 250);
          })();
        `}
      </Script>

      <div className="pointer-events-none absolute left-[-12rem] top-[-8rem] h-[30rem] w-[30rem] rounded-full bg-cyan-400/20 blur-3xl" />
      <div className="pointer-events-none absolute right-[-10rem] bottom-[-10rem] h-[32rem] w-[32rem] rounded-full bg-fuchsia-500/20 blur-3xl" />

      <div className="mx-auto max-w-5xl space-y-6">
        <nav className="flex items-center justify-between rounded-full border border-white/10 bg-white/[.04] px-5 py-3 backdrop-blur-xl">
          <Link href="/" className="flex items-center gap-2 font-black tracking-tight text-white">
            <span className="grid h-9 w-9 place-items-center rounded-full bg-cyan-300 text-slate-950">🦞</span>
            ClawAudit
          </Link>
          <Button asChild variant="outline" size="sm">
            <Link href="/"><ArrowLeft className="h-4 w-4" /> Back to audit</Link>
          </Button>
        </nav>

        <section className="relative overflow-hidden rounded-[1.75rem] border border-white/10 bg-slate-950/70 p-6 shadow-2xl shadow-black/30 backdrop-blur-xl md:p-8">
          <div className="absolute right-8 top-8 text-cyan-300/20">
            <Sparkles size={108} />
          </div>
          <Badge className="mb-4" variant="default">Support the project</Badge>
          <h1 className="max-w-3xl text-4xl font-black tracking-tight text-white md:text-6xl">
            Help keep ClawAudit sharp<span className="text-cyan-300">.</span>
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
            If ClawAudit saves you time, helps you trust your automations, or gives you cleaner control over your agent setup, you can support continued improvements here.
          </p>

          <div className="mt-6 grid gap-5 lg:grid-cols-[1fr_.9fr] lg:items-center">
            <Card className="bg-white/[.05]">
              <CardHeader>
                <CardTitle>Make a donation</CardTitle>
                <CardDescription>Use the secure PayPal button below to support continued work.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-2xl border border-white/10 bg-white p-4 text-slate-950 shadow-xl shadow-black/20">
                  <div id={paypalContainerId} />
                </div>
              </CardContent>
            </Card>

            <div className="space-y-3 rounded-2xl border border-cyan-300/20 bg-cyan-300/10 p-5 text-cyan-50">
              <div className="font-bold">Thank you for backing ClawAudit.</div>
              <p className="text-sm leading-6 text-cyan-100/85">
                Every contribution helps improve the audit experience, add better tracking, and keep the project polished for real-world use.
              </p>
              <Button asChild variant="outline" size="lg">
                <Link href="/">View audit dashboard</Link>
              </Button>
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <SupportCard icon={<ShieldCheck />} title="Safer autonomy" text="More checks, clearer alerts, and better preflight confidence." />
          <SupportCard icon={<Star />} title="Better experience" text="Sharper visuals, smoother flows, and cleaner reports." />
          <SupportCard icon={<Sparkles />} title="More features" text="Automation maps, suggested fixes, and stronger review tools." />
        </section>
      </div>
    </main>
  );
}

function SupportCard({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <Card className="bg-white/[.05]">
      <CardHeader>
        <div className="mb-3 grid h-12 w-12 place-items-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10 text-cyan-200">{icon}</div>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{text}</CardDescription>
      </CardHeader>
      <CardContent />
    </Card>
  );
}

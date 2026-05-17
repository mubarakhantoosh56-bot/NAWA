"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowUpLeft,
  BrainCircuit,
  Building2,
  CheckCircle2,
  ChevronLeft,
  Database,
  Factory,
  FileSearch,
  Gauge,
  Landmark,
  LineChart,
  LockKeyhole,
  Network,
  Orbit,
  ShieldCheck,
  UsersRound,
  Workflow,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const navItems = [
  { label: "Platform", ar: "المنصة" },
  { label: "Workforce", ar: "فرق العمل" },
  { label: "Intelligence", ar: "الاستخبارات" },
];

const departments = [
  { name: "Finance", ar: "المالية", detail: "Margin, cash, and variance signals in one operating view.", icon: Landmark },
  { name: "Revenue", ar: "الإيرادات", detail: "Priority accounts, pipeline risk, and next best action.", icon: UsersRound },
  { name: "Operations", ar: "العمليات", detail: "Early warnings before friction becomes failure.", icon: Factory },
  { name: "Knowledge", ar: "المعرفة", detail: "Trusted institutional memory, available at decision speed.", icon: FileSearch },
];

const intelligence = [
  { en: "Executive decisions connected to operational context.", ar: "قرارات تنفيذية مرتبطة بسياق العمل." },
  { en: "Institutional memory that understands teams, files, and permissions.", ar: "ذاكرة مؤسسية تفهم الفرق والملفات والصلاحيات." },
  { en: "A quiet system of intelligence, built for daily command.", ar: "نظام ذكاء هادئ لإدارة الإيقاع اليومي." },
];

const dashboardRows = [
  ["Revenue growth", "نمو الإيرادات", "+18.4%", "Stable", "text-teal-200"],
  ["Operating cost", "تكلفة التشغيل", "-7.2%", "Review", "text-gold"],
  ["Response time", "زمن الاستجابة", "2.8m", "On target", "text-teal-200"],
  ["Data readiness", "جاهزية البيانات", "94%", "Trusted", "text-white"],
];

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0 },
};

export default function LandingPage() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#070d16] text-white">
      <div className="pointer-events-none fixed inset-0 opacity-80">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_10%,rgba(21,94,117,0.13),transparent_30rem),radial-gradient(circle_at_12%_46%,rgba(181,139,74,0.07),transparent_26rem),linear-gradient(180deg,#070d16_0%,#0a111d_48%,#070b12_100%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.022)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.022)_1px,transparent_1px)] bg-[size:96px_96px] opacity-[0.08]" />
      </div>

      <div className="relative">
        <Navbar />
        <HeroSection />
        <DepartmentsSection />
        <OperationalSection />
        <DashboardShowcase />
        <EnterpriseArchitectureSection />
        <CtaFooter />
      </div>
    </main>
  );
}

function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-[#070d16]/72 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3.5 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] text-xs font-semibold text-teal-100">
            N
          </span>
          <span className="flex items-baseline gap-2">
            <span className="text-sm font-semibold tracking-normal text-white">NAWA</span>
            <span dir="rtl" className="text-xs font-medium text-white/36">
              نواة
            </span>
          </span>
        </Link>

        <div className="hidden items-center gap-1 lg:flex">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={`#${item.label}`}
              className="flex items-baseline gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium text-white/48 transition hover:bg-white/[0.045] hover:text-white/82"
            >
              <span>{item.label}</span>
              <span dir="rtl" className="font-normal text-white/28">
                {item.ar}
              </span>
            </a>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild variant="executive" size="sm">
            <Link href="/login">
              Request Access
              <ChevronLeft className="h-3.5 w-3.5 rotate-180" />
            </Link>
          </Button>
        </div>
      </nav>
    </header>
  );
}

function HeroSection() {
  return (
    <section id="Platform" className="mx-auto grid min-h-[calc(100vh-61px)] max-w-7xl items-center gap-16 px-5 py-24 sm:px-6 lg:grid-cols-[0.82fr_1fr] lg:px-8 lg:py-28">
      <motion.div initial="hidden" animate="visible" variants={fadeUp} transition={{ duration: 0.7, ease: "easeOut" }} className="max-w-xl">
        <div className="flex items-baseline gap-3 text-sm font-semibold text-white/64">
          <span>NAWA</span>
          <span dir="rtl" className="text-xs font-medium text-white/36">
            نواة
          </span>
        </div>
        <h1 className="mt-7 max-w-xl text-5xl font-semibold leading-[1.03] text-white sm:text-6xl lg:text-[4.65rem]">
          Enterprise Intelligence
          <span className="block text-white/72">Built for execution.</span>
        </h1>
        <p className="mt-7 max-w-md text-base leading-8 text-white/52 sm:text-lg">
          Transform company knowledge into operational intelligence.
        </p>
        <p dir="rtl" className="mt-3 max-w-md text-sm leading-7 text-white/38">
          حوّل معرفة الشركة إلى استخبارات تشغيلية قابلة للتنفيذ.
        </p>
        <div className="mt-9 flex flex-col gap-3 sm:flex-row">
          <Button asChild>
            <a href="#Dashboard">
              View Platform
              <ArrowUpLeft className="h-3.5 w-3.5" />
            </a>
          </Button>
          <Button asChild variant="executive">
            <Link href="/login">Request Access</Link>
          </Button>
        </div>
        <div className="mt-14 grid max-w-md grid-cols-3 gap-5 border-t border-white/[0.07] pt-6">
          {[
            ["Decision speed", "سرعة القرار"],
            ["Operational memory", "ذاكرة تشغيلية"],
            ["Governed access", "وصول محكوم"],
          ].map(([item, ar]) => (
            <div key={item} className="text-xs font-medium leading-5 text-white/42">
              <CheckCircle2 className="mb-3 h-3.5 w-3.5 text-teal-200/80" />
              <span className="block">{item}</span>
              <span dir="rtl" className="mt-1 block text-[11px] font-normal text-white/28">
                {ar}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
        className="mx-auto w-full max-w-2xl lg:justify-self-end"
      >
        <OperatingDashboard />
      </motion.div>
    </section>
  );
}

function OperatingDashboard() {
  return (
    <div className="relative scale-[0.96]">
      <div className="absolute -inset-6 rounded-[2rem] bg-teal-400/[0.055] blur-3xl" />
      <div className="relative overflow-hidden rounded-md border border-white/[0.08] bg-[#09121f]/88 shadow-[0_28px_80px_rgba(0,0,0,0.34)]">
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4">
          <div className="flex items-center gap-2 text-xs font-medium text-white/42">
            <span className="h-2 w-2 rounded-full bg-gold/70" />
            <span>Executive command</span>
            <span dir="rtl" className="text-white/28">
              غرفة القيادة
            </span>
          </div>
          <div className="flex gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-white/14" />
            <span className="h-1.5 w-1.5 rounded-full bg-white/14" />
            <span className="h-1.5 w-1.5 rounded-full bg-white/14" />
          </div>
        </div>

        <div className="grid gap-4 p-4 lg:grid-cols-[190px_1fr]">
          <aside className="space-y-2.5 border-r border-white/[0.07] pr-4">
            {[
              ["Command", "القيادة"],
              ["Finance", "المالية"],
              ["Revenue", "الإيرادات"],
              ["Operations", "العمليات"],
            ].map(([item, ar], index) => (
              <div key={item} className={`rounded-md px-3 py-2 text-xs font-medium ${index === 0 ? "bg-teal-300/[0.08] text-teal-100" : "bg-white/[0.025] text-white/42"}`}>
                <span>{item}</span>
                <span dir="rtl" className="ml-1.5 text-white/28">
                  {ar}
                </span>
              </div>
            ))}
            <div className="rounded-md bg-gold/[0.075] p-3">
              <div className="flex items-baseline gap-1.5 text-xs font-semibold text-gold/90">
                <span>Signal</span>
                <span dir="rtl" className="font-normal text-gold/55">
                  إشارة
                </span>
              </div>
              <p className="mt-2 text-xs leading-6 text-white/58">A supplier delay is elevating support pressure.</p>
            </div>
          </aside>

          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                ["Health", "الصحة", "87%", Gauge],
                ["Decisions", "القرارات", "12", BrainCircuit],
                ["Sources", "المصادر", "348", Database],
              ].map(([label, ar, value, Icon]) => (
                <div key={label as string} className="rounded-md bg-white/[0.035] p-4">
                  <Icon className="h-3.5 w-3.5 text-teal-200/80" />
                  <div className="mt-5 text-2xl font-semibold">{value as string}</div>
                  <div className="mt-1 flex items-baseline gap-1.5 text-xs font-medium text-white/36">
                    <span>{label as string}</span>
                    <span dir="rtl" className="text-white/24">
                      {ar as string}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div className="grid gap-3 lg:grid-cols-[1fr_210px]">
              <div className="rounded-md bg-white/[0.03] p-4">
                <div className="flex items-center justify-between">
                  <span className="flex items-baseline gap-2 text-sm font-semibold text-white/88">
                    Operating pulse
                    <span dir="rtl" className="text-xs font-normal text-white/30">
                      نبض التشغيل
                    </span>
                  </span>
                  <span className="rounded bg-teal-300/[0.08] px-2 py-1 text-xs font-medium text-teal-100/80">Live</span>
                </div>
                <div className="mt-6 flex h-36 items-end gap-2">
                  {[46, 62, 55, 73, 69, 86, 78, 91, 84, 96, 88, 93].map((height, index) => (
                    <motion.span
                      key={index}
                      initial={{ height: 12 }}
                      animate={{ height }}
                      transition={{ duration: 0.9, delay: index * 0.04 }}
                      className="flex-1 rounded-t bg-gradient-to-t from-teal-500/30 to-teal-200/75"
                    />
                  ))}
                </div>
              </div>

              <div className="rounded-md bg-white/[0.03] p-4">
                <div className="flex items-baseline gap-2 text-sm font-semibold text-white/88">
                  Decision path
                  <span dir="rtl" className="text-xs font-normal text-white/30">
                    مسار القرار
                  </span>
                </div>
                <div className="mt-5 space-y-3">
                  {[
                    ["Context", "سياق"],
                    ["Risk", "مخاطر"],
                    ["Action", "تنفيذ"],
                  ].map(([item, ar]) => (
                    <div key={item} className="flex items-center gap-3 text-xs font-medium text-white/48">
                      <span className="h-1.5 w-1.5 rounded-full bg-gold/80" />
                      <span>{item}</span>
                      <span dir="rtl" className="text-white/24">
                        {ar}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="rounded-md bg-[#07101b]/88">
              {dashboardRows.map(([metric, ar, value, status, tone]) => (
                <div key={metric} className="grid grid-cols-3 gap-3 border-b border-white/[0.055] px-4 py-3 last:border-b-0">
                  <span className="text-xs font-medium text-white/48">
                    <span className="block">{metric}</span>
                    <span dir="rtl" className="mt-1 block text-[11px] font-normal text-white/24">
                      {ar}
                    </span>
                  </span>
                  <span className={`text-xs font-semibold ${tone}`}>{value}</span>
                  <span className="text-xs font-medium text-white/32">{status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DepartmentsSection() {
  return (
    <section id="Workforce" className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
      <SectionIntro eyebrow="AI Workforce" title="Specialized intelligence for every function." text="Each team gets a focused operating layer tuned to its work, data, and decisions." ar="طبقة تشغيل مركزة لكل فريق، متصلة بعمله وقراراته." />
      <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {departments.map(({ name, ar, detail, icon: Icon }, index) => (
          <motion.div key={name} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.3 }} variants={fadeUp} transition={{ duration: 0.5, delay: index * 0.06 }}>
            <Card className="h-full transition duration-300 hover:-translate-y-1 hover:border-teal-200/25 hover:bg-white/[0.075]">
              <CardHeader className="p-6">
                <Icon className="h-5 w-5 text-gold" />
                <CardTitle className="mt-6 text-lg">
                  {name}
                  <span dir="rtl" className="ml-2 text-sm font-medium text-white/32">
                    {ar}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="px-6 pb-6">
                <p className="text-sm leading-7 text-white/50">{detail}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

function OperationalSection() {
  return (
    <section id="Intelligence" className="border-y border-white/10 bg-white/[0.025]">
      <div className="mx-auto grid max-w-7xl gap-14 px-4 py-24 sm:px-6 lg:grid-cols-[0.95fr_1.05fr] lg:px-8">
        <SectionIntro eyebrow="Operational Intelligence" title="From scattered data to institutional command." text="NAWA reads signals, understands constraints, and moves decisions into action." ar="تقرأ نواة الإشارات، تفهم القيود، وتحوّل القرار إلى فعل." />
        <div className="space-y-4">
          {intelligence.map((item, index) => (
            <motion.div key={item.en} initial={{ opacity: 0, x: -18 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ duration: 0.45, delay: index * 0.08 }} className="rounded-md border border-white/10 bg-[#09121f]/80 p-6">
              <div className="flex items-start gap-4">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-teal-300/20 bg-teal-300/10">
                  <Workflow className="h-4 w-4 text-teal-100" />
                </span>
                <p className="text-lg leading-8 text-white/70">
                  {item.en}
                  <span dir="rtl" className="mt-1 block text-sm font-normal text-white/36">
                    {item.ar}
                  </span>
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function DashboardShowcase() {
  return (
    <section id="Dashboard" className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
      <SectionIntro eyebrow="Dashboard Showcase" title="Information density without congestion." text="A command interface for daily operating rhythm, built with precision and restraint." ar="واجهة قيادة يومية، دقيقة وهادئة." />
      <div className="mt-12 grid gap-5 lg:grid-cols-[1fr_360px]">
        <div className="rounded-md border border-white/10 bg-[#09121f]/88 p-6">
          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["Critical requests", "طلبات حرجة"],
              ["Contract risk", "مخاطر العقود"],
              ["Growth signals", "إشارات النمو"],
            ].map(([item, ar], index) => (
              <div key={item} className="rounded-md border border-white/10 bg-white/[0.04] p-5">
                <LineChart className="h-4 w-4 text-teal-200" />
                <div className="mt-6 text-sm font-medium text-white/46">{item}</div>
                <div dir="rtl" className="mt-1 text-xs text-white/26">
                  {ar}
                </div>
                <div className="mt-2 text-3xl font-semibold">{[24, 7, 31][index]}</div>
              </div>
            ))}
          </div>
          <div className="mt-5 rounded-md border border-white/10 bg-[#070d16] p-5">
            <div className="mb-6 flex items-center justify-between">
              <span className="flex items-baseline gap-2 text-sm font-semibold">
                Decision chain
                <span dir="rtl" className="text-xs font-normal text-white/30">
                  سلسلة القرار
                </span>
              </span>
              <ShieldCheck className="h-4 w-4 text-gold" />
            </div>
            <div className="grid gap-3 md:grid-cols-4">
              {[
                ["Source", "مصدر"],
                ["Verify", "تحقق"],
                ["Infer", "استنتاج"],
                ["Execute", "تنفيذ"],
              ].map(([step, ar]) => (
                <div key={step} className="rounded-md border border-white/8 bg-white/[0.035] p-4 text-sm font-medium text-white/58">
                  {step}
                  <span dir="rtl" className="ml-1.5 text-xs font-normal text-white/26">
                    {ar}
                  </span>
                  <div className="mt-4 h-1.5 rounded bg-teal-300/30">
                    <div className="h-full w-3/4 rounded bg-teal-200" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <Card>
          <CardHeader className="p-6">
            <Network className="h-5 w-5 text-gold" />
            <CardTitle className="mt-6 text-lg">Institutional connection layer</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 px-6 pb-6">
            {[
              ["Company files", "ملفات الشركة"],
              ["Team memory", "ذاكرة الفرق"],
              ["User permissions", "صلاحيات المستخدمين"],
              ["Auditable output", "مخرجات قابلة للتدقيق"],
            ].map(([item, ar]) => (
              <div key={item} className="flex items-center justify-between rounded-md border border-white/8 bg-white/[0.035] px-3.5 py-3 text-sm font-medium text-white/55">
                <span>
                  {item}
                  <span dir="rtl" className="ml-2 text-xs font-normal text-white/28">
                    {ar}
                  </span>
                </span>
                <LockKeyhole className="h-3.5 w-3.5 text-teal-200" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function EnterpriseArchitectureSection() {
  return (
    <section id="Architecture" className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
      <div className="grid gap-10 rounded-md border border-white/10 bg-white/[0.035] p-7 sm:p-10 lg:grid-cols-[0.8fr_1.2fr]">
        <div>
          <div className="flex items-baseline gap-2 text-xs font-semibold uppercase text-gold">
            Enterprise Architecture
            <span dir="rtl" className="font-normal normal-case text-gold/55">
              بنية مؤسسية
            </span>
          </div>
          <h2 className="mt-5 text-4xl font-semibold leading-[1.14] sm:text-5xl">Intelligence as infrastructure.</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {[
            ["Native workflow", "سير عمل أصيل", "Built into how decisions move."],
            ["Institutional context", "سياق مؤسسي", "Understands the operating model."],
            ["Governed access", "وصول محكوم", "Trust inside clear boundaries."],
          ].map(([title, ar, text]) => (
            <div key={title} className="rounded-md border border-white/10 bg-[#07101b]/80 p-5">
              <Building2 className="h-4 w-4 text-teal-200" />
              <h3 className="mt-5 font-semibold">
                {title}
                <span dir="rtl" className="ml-2 text-sm font-medium text-white/32">
                  {ar}
                </span>
              </h3>
              <p className="mt-3 text-sm leading-7 text-white/50">{text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CtaFooter() {
  return (
    <footer className="border-t border-white/10 px-4 py-20 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col justify-between gap-10 lg:flex-row lg:items-end">
        <div>
          <Orbit className="h-6 w-6 text-gold" />
          <h2 className="mt-6 max-w-2xl text-4xl font-semibold leading-[1.14] sm:text-5xl">
            Quieter operations. Stronger decisions.
          </h2>
          <p className="mt-5 max-w-lg text-lg leading-8 text-white/52">Start with an intelligence layer designed for execution.</p>
          <p dir="rtl" className="mt-2 max-w-lg text-sm leading-7 text-white/34">
            طبقة ذكاء مصممة للتنفيذ، بثقة وهدوء.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button asChild>
            <a href="#Dashboard">View Platform</a>
          </Button>
          <Button asChild variant="executive">
            <Link href="/login">Request Access</Link>
          </Button>
        </div>
      </div>
    </footer>
  );
}

function SectionIntro({ eyebrow, title, text, ar }: { eyebrow: string; title: string; text: string; ar?: string }) {
  return (
    <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.4 }} variants={fadeUp} transition={{ duration: 0.55 }} className="max-w-3xl">
      <div className="text-xs font-semibold uppercase text-gold">{eyebrow}</div>
      <h2 className="mt-5 text-4xl font-semibold leading-[1.14] sm:text-5xl">{title}</h2>
      <p className="mt-5 max-w-xl text-lg leading-8 text-white/52">{text}</p>
      {ar ? (
        <p dir="rtl" className="mt-2 max-w-xl text-sm leading-7 text-white/34">
          {ar}
        </p>
      ) : null}
    </motion.div>
  );
}

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import { api } from "../lib/api";
import { Logo, Spinner } from "../components/ui";
import Certificate from "../components/Certificate";

/** Публичная проверка сертификата по номеру: /verify/AIA-XXXX-XXXX-XXXX */
export default function Verify({ certId }) {
  const [state, setState] = useState({ loading: true });
  useEffect(() => {
    api(`/api/certificates/${encodeURIComponent(certId)}`)
      .then((r) => setState({ cert: r.certificate }))
      .catch((e) => setState({ error: e.message }));
  }, [certId]);

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl space-y-6 px-4 py-10">
        <a href="/" className="no-print inline-flex items-center gap-3">
          <Logo />
          <span className="text-lg font-extrabold">AI Anki</span>
        </a>
        {state.loading ? (
          <div className="flex justify-center py-20"><Spinner className="h-6 w-6" /></div>
        ) : state.cert ? (
          <>
            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="no-print flex items-center gap-3 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-5 py-4">
              <ShieldCheck className="h-6 w-6 text-emerald-300" />
              <div>
                <div className="font-semibold text-emerald-100">Сертификат подлинный</div>
                <div className="text-sm text-emerald-200/70">№ {state.cert.id} выдан платформой AI Anki и записан в её реестре.</div>
              </div>
            </motion.div>
            <Certificate cert={state.cert} actions={false} />
          </>
        ) : (
          <div className="flex items-center gap-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-4">
            <ShieldAlert className="h-6 w-6 text-rose-300" />
            <div>
              <div className="font-semibold text-rose-100">Сертификат не найден</div>
              <div className="text-sm text-rose-200/70">Проверьте номер: {certId}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

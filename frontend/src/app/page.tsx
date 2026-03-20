"use client";

import React, { useState } from "react";
import { ShieldCheck, CloudLightning, Sun, MapPinOff, AlertTriangle, CheckCircle, IndianRupee, Activity, Navigation, Zap, Calendar, TrendingUp } from "lucide-react";

export default function Dashboard() {
  const [riderState, setRiderState] = useState({
    rider_id: "RIDER_8023",
    profile: {
      name: "Ravi Kumar",
      phone: "+91-9876543210",
      vehicle_type: "2_WHEELER",
      primary_zone: "BLR_INDIRANAGAR",
    },
    real_time_state: {
      status: "ONLINE",
      current_location: { lat: 12.9784, lon: 77.6408 },
      last_ping_timestamp: "2026-03-16T20:54:00Z",
    },
    daily_performance: {
      orders_completed_today: 14,
      daily_target: 18,
      incentive_at_risk: 250.00,
      earnings_today: 650.00,
    },
    insurance_profile: {
      policy_active: true,
      weekly_premium_paid: 22.50,
      risk_score: 0.85,
    },
    fraud_telemetry: {
      current_speed_kmph: 0.0,
      is_mock_location_enabled: false,
      battery_level: 45,
    },
  });

  const [modalData, setModalData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const triggerClaim = async (disruption: any, spoofGPS: boolean = false) => {
    setLoading(true);
    setModalData(null);
    const mockRiderState = { ...riderState };
    if (spoofGPS) {
      mockRiderState.fraud_telemetry.is_mock_location_enabled = true;
    }
    const payload = {
      rider_id: mockRiderState.rider_id,
      disruption,
    };

    try {
      const response = await fetch("http://localhost:8000/evaluate_claim", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      setModalData(data);
    } catch (error) {
      setModalData({ claim_status: "ERROR", reason: "Connection failed to backend API", payout_amount: 0 });
    } finally {
      if (spoofGPS) {
        mockRiderState.fraud_telemetry.is_mock_location_enabled = false;
      }
      setRiderState(mockRiderState);
      setLoading(false);
    }
  };

  const progressPercentage = Math.min(
    (riderState.daily_performance.orders_completed_today / riderState.daily_performance.daily_target) * 100,
    100
  );

  return (
    <div className="min-h-screen bg-[#07090E] text-slate-200 font-sans selection:bg-indigo-500/30 overflow-x-hidden pb-12">
      {/* Dynamic Background Gradients */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-indigo-600/10 blur-[150px] rounded-full mix-blend-screen" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[60%] bg-emerald-600/10 blur-[130px] rounded-full mix-blend-screen" />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto flex flex-col lg:flex-row gap-8 p-4 md:p-8 lg:py-16">
        
        {/* Main Dashboard Panel */}
        <main className="flex-1 space-y-6 lg:min-w-[600px]">
          <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold uppercase tracking-widest mb-4 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                LIVE • {riderState.real_time_state.status}
              </div>
              <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-br from-white via-slate-200 to-slate-500 bg-clip-text text-transparent">
                Rider Hub
              </h1>
              <p className="text-slate-400 mt-2 flex items-center gap-2 text-sm tracking-wide">
                <span className="font-semibold text-slate-200">{riderState.profile.name}</span>
                <span className="w-1 h-1 bg-slate-600 rounded-full" />
                <span>{riderState.profile.vehicle_type}</span>
                <span className="w-1 h-1 bg-slate-600 rounded-full" />
                <span className="flex items-center gap-1.5"><Navigation className="w-3.5 h-3.5" /> {riderState.profile.primary_zone}</span>
              </p>
            </div>
            
            <div className="text-left md:text-right mt-4 md:mt-0 p-4 md:p-0 rounded-2xl md:bg-transparent bg-white/5 border md:border-none border-white/5">
              <p className="text-xs text-slate-500 uppercase tracking-widest font-semibold mb-1">Today's Earnings</p>
              <p className="text-3xl font-extrabold flex items-center justify-start md:justify-end text-emerald-400 drop-shadow-[0_0_10px_rgba(52,211,153,0.3)]">
                <IndianRupee className="w-6 h-6 mr-1" />
                {riderState.daily_performance.earnings_today}
              </p>
            </div>
          </header>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Weekly Coverage Card */}
            {riderState.insurance_profile.policy_active && (
              <div className="group relative overflow-hidden bg-slate-900/40 backdrop-blur-2xl border border-slate-700/50 hover:border-indigo-500/50 rounded-3xl p-6 transition-all duration-300 hover:-translate-y-1 block hover:bg-slate-800/60 hover:shadow-[0_0_40px_rgba(99,102,241,0.15)] flex flex-col justify-between">
                <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 blur-[40px] rounded-full -mr-10 -mt-10 transition-transform duration-700 group-hover:scale-150" />
                <div className="flex items-start justify-between relative z-10">
                  <div className="p-3.5 rounded-2xl bg-indigo-500/20 text-indigo-400 ring-1 ring-inset ring-indigo-500/30">
                    <ShieldCheck className="w-6 h-6" />
                  </div>
                  <span className="px-3.5 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-bold ring-1 ring-inset ring-emerald-500/30">
                    Active
                  </span>
                </div>
                <div className="mt-8 relative z-10">
                  <h3 className="text-lg font-bold text-slate-100">Parametric Coverage</h3>
                  <p className="text-sm text-slate-400 mt-1 font-medium flex items-center gap-1.5">
                    <Calendar className="w-4 h-4 text-slate-500" /> Premium Paid: 
                    <span className="text-slate-200">₹{riderState.insurance_profile.weekly_premium_paid}</span>
                  </p>
                </div>
              </div>
            )}

            {/* Protected Income Card */}
            <div className="group relative overflow-hidden bg-gradient-to-br from-indigo-600 via-indigo-700 to-violet-800 rounded-3xl p-6 border border-indigo-400/30 transition-all duration-300 hover:shadow-[0_10px_40px_rgba(99,102,241,0.4)] hover:-translate-y-1">
              <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10 mix-blend-overlay" />
              <div className="absolute -bottom-10 -right-10 w-48 h-48 bg-white/10 blur-[30px] rounded-full transition-transform duration-700 group-hover:scale-110" />
              
              <div className="flex items-start justify-between relative z-10">
                <div className="p-3.5 rounded-2xl bg-white/10 text-white ring-1 ring-inset ring-white/20 backdrop-blur-md">
                  <Zap className="w-6 h-6 drop-shadow-md" />
                </div>
              </div>
              <div className="mt-8 relative z-10">
                <h3 className="text-xs font-bold text-indigo-200 uppercase tracking-widest mb-1 opacity-90">Protected Incentive</h3>
                <p className="text-4xl md:text-5xl font-extrabold text-white flex items-center drop-shadow-xl">
                  <IndianRupee className="w-8 h-8 md:w-10 md:h-10 mr-1 opacity-90" />
                  {riderState.daily_performance.incentive_at_risk}
                </p>
              </div>
            </div>
          </div>

          {/* Daily Target Progress */}
          <div className="bg-slate-900/40 backdrop-blur-2xl border border-slate-700/50 rounded-3xl p-6 md:p-8 mt-5">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-sm font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-400" /> Target Progress
              </h2>
              <span className="text-sm font-bold text-slate-400 bg-slate-800/80 px-3 py-1 rounded-full border border-slate-700/50">
                <span className="text-slate-200">{riderState.daily_performance.orders_completed_today}</span> / {riderState.daily_performance.daily_target}
              </span>
            </div>
            <div className="w-full bg-slate-950/80 rounded-full h-3.5 ring-1 ring-inset ring-slate-800/80 overflow-hidden shadow-inner relative">
              <div
                className="absolute top-0 left-0 bottom-0 bg-gradient-to-r from-blue-600 via-indigo-500 to-indigo-400 rounded-full transition-all duration-1000 ease-out shadow-[0_0_15px_rgba(99,102,241,0.5)]"
                style={{ width: `${progressPercentage}%` }}
              >
                <div className="absolute top-0 right-0 bottom-0 w-20 bg-gradient-to-r from-transparent to-white/30 skew-x-12 translate-x-4 mix-blend-overlay" />
              </div>
            </div>
          </div>

          {/* Results Modal / Notification Area */}
          <div className={`transition-all duration-500 ease-out origin-top ${modalData ? 'scale-100 opacity-100 h-auto mt-6' : 'scale-95 opacity-0 h-0 overflow-hidden mt-0'}`}>
            {modalData && (
              <div className={`p-6 rounded-3xl backdrop-blur-2xl flex flex-col md:flex-row gap-5 items-start md:items-center relative overflow-hidden ${
                modalData.claim_status === 'APPROVED' 
                  ? 'bg-emerald-950/30 border border-emerald-500/30 shadow-[0_0_30px_rgba(16,185,129,0.1)]' 
                  : modalData.claim_status === 'REJECTED' || modalData.claim_status === 'FRAUD_FLAGGED' || modalData.claim_status === 'DENIED' || modalData.claim_status === 'ERROR'
                  ? 'bg-rose-950/30 border border-rose-500/30 shadow-[0_0_30px_rgba(225,29,72,0.1)]' 
                  : 'bg-amber-950/30 border border-amber-500/30 shadow-[0_0_30px_rgba(245,158,11,0.1)]'
              }`}>
                {/* Background glow for modal */}
                <div className={`absolute top-1/2 left-0 -translate-y-1/2 w-32 h-32 blur-[60px] rounded-full pointer-events-none ${
                    modalData.claim_status === 'APPROVED' ? 'bg-emerald-500/20' 
                    : modalData.claim_status === 'REJECTED' || modalData.claim_status === 'FRAUD_FLAGGED' || modalData.claim_status === 'DENIED' || modalData.claim_status === 'ERROR' ? 'bg-rose-500/20'
                    : 'bg-amber-500/20'
                }`} />

                <div className={`p-4 rounded-2xl flex-shrink-0 z-10 ${
                  modalData.claim_status === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/30' 
                  : modalData.claim_status === 'REJECTED' || modalData.claim_status === 'FRAUD_FLAGGED' || modalData.claim_status === 'DENIED' || modalData.claim_status === 'ERROR' ? 'bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/30'
                  : 'bg-amber-500/20 text-amber-400 ring-1 ring-amber-500/30'
                }`}>
                  {modalData.claim_status === 'APPROVED' ? <CheckCircle className="w-8 h-8 flex-shrink-0 drop-shadow-md" /> : <AlertTriangle className="w-8 h-8 flex-shrink-0 drop-shadow-md" />}
                </div>

                <div className="flex-1 w-full z-10">
                  <h3 className={`text-xl font-extrabold tracking-tight ${
                    modalData.claim_status === 'APPROVED' ? 'text-emerald-400' 
                    : modalData.claim_status === 'REJECTED' || modalData.claim_status === 'FRAUD_FLAGGED' || modalData.claim_status === 'DENIED' || modalData.claim_status === 'ERROR' ? 'text-rose-400'
                    : 'text-amber-400'
                  }`}>
                    {modalData.claim_status}
                  </h3>
                  <p className="text-sm mt-1.5 text-slate-300 leading-relaxed font-medium">{modalData.reason}</p>
                </div>
                
                {modalData.payout_amount !== undefined && modalData.payout_amount > 0 && (
                  <div className="mt-4 md:mt-0 pt-4 md:pt-0 border-t md:border-t-0 md:border-l border-slate-700/50 md:pl-6 w-full md:w-auto flex flex-row md:flex-col items-center md:items-start justify-between z-10">
                    <span className="text-xs font-bold text-emerald-400/70 uppercase tracking-widest mb-1">Payout</span>
                    <span className="text-3xl font-black text-emerald-400 flex items-center drop-shadow-[0_0_12px_rgba(52,211,153,0.4)]">
                      <IndianRupee className="w-6 h-6 mr-1" />{modalData.payout_amount}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>

        {/* Action Panel Sidebar */}
        <aside className="w-full lg:w-[400px] bg-slate-900/40 backdrop-blur-3xl border border-slate-700/50 rounded-3xl p-6 shadow-2xl flex flex-col h-fit sticky top-8">
          <div className="mb-8">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-2">
              <Activity className="w-5 h-5 text-indigo-400" /> Disruption Simulator
            </h2>
            <p className="text-xs text-slate-400 leading-relaxed max-w-sm">
              Secured testing environment. Inject external events to dry-run the LangGraph parametric risk model and LLM fraud detection nodes.
            </p>
          </div>
          
          <div className="flex flex-col gap-3">
            <button
              onClick={() => triggerClaim({ type: "EXTREME_WEATHER", intensity_value: 45, zone: "BLR_INDIRANAGAR" })}
              disabled={loading}
              className="group relative flex items-center justify-between w-full p-4 rounded-2xl bg-gradient-to-r from-blue-950/40 to-blue-900/20 border border-blue-500/20 hover:border-blue-500/60 hover:from-blue-900/60 hover:to-blue-800/40 text-blue-100 transition-all duration-300 overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-[0_0_20px_rgba(59,130,246,0.15)] focus:ring-2 focus:ring-blue-500/50 outline-none"
            >
              <div className="absolute inset-0 w-0 bg-blue-500/10 transition-all duration-500 ease-out group-hover:w-full" />
              <div className="flex items-center gap-4 relative z-10">
                <div className="p-2.5 bg-blue-500/20 rounded-xl text-blue-400 group-hover:bg-blue-500/40 group-hover:text-blue-100 transition-colors ring-1 ring-inset ring-blue-500/30">
                  <CloudLightning className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <div className="font-bold text-sm text-blue-50">Extreme Rain</div>
                  <div className="text-xs text-blue-300/80 font-medium mt-0.5">Intensity: 45mm</div>
                </div>
              </div>
              <div className="relative z-10 text-blue-500/50 group-hover:text-blue-400 group-hover:translate-x-1 transition-all">
                <Navigation className="w-4 h-4 rotate-90" />
              </div>
            </button>

            <button
              onClick={() => triggerClaim({ type: "EXTREME_WEATHER", intensity_value: 5, zone: "BLR_INDIRANAGAR" })}
              disabled={loading}
              className="group relative flex items-center justify-between w-full p-4 rounded-2xl bg-gradient-to-r from-slate-800/40 to-slate-800/20 border border-slate-600/30 hover:border-slate-500 focus:ring-2 focus:ring-slate-500/50 hover:from-slate-700/60 hover:to-slate-700/40 text-slate-100 transition-all duration-300 overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed outline-none hover:shadow-[0_0_20px_rgba(148,163,184,0.1)] mt-1"
            >
              <div className="absolute inset-0 w-0 bg-slate-500/10 transition-all duration-500 ease-out group-hover:w-full" />
              <div className="flex items-center gap-4 relative z-10">
                <div className="p-2.5 bg-slate-700/50 rounded-xl text-slate-300 group-hover:bg-slate-600/80 group-hover:text-white transition-colors ring-1 ring-inset ring-slate-500/40">
                  <Sun className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <div className="font-bold text-sm text-slate-100">Clear Weather</div>
                  <div className="text-xs text-slate-400 font-medium mt-0.5">Intensity: 5.0 (Parametric Fail)</div>
                </div>
              </div>
              <div className="relative z-10 text-slate-600 group-hover:text-slate-400 group-hover:translate-x-1 transition-all">
                <Navigation className="w-4 h-4 rotate-90" />
              </div>
            </button>

            <div className="mt-4 pt-4 border-t border-slate-700/50 border-dashed">
              <button
                onClick={() => triggerClaim({ type: "EXTREME_WEATHER", intensity_value: 45, zone: "BLR_INDIRANAGAR" }, true)}
                disabled={loading}
                className="group relative flex items-center justify-between w-full p-4 rounded-2xl bg-gradient-to-r from-rose-950/40 to-rose-900/20 border border-rose-500/30 hover:border-rose-500/60 focus:ring-2 focus:ring-rose-500/50 hover:from-rose-900/60 hover:to-rose-800/40 text-rose-100 transition-all duration-300 overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-[0_0_20px_rgba(225,29,72,0.15)] outline-none"
              >
                <div className="absolute inset-0 w-0 bg-rose-500/10 transition-all duration-500 ease-out group-hover:w-full" />
                <div className="flex items-center gap-4 relative z-10">
                  <div className="p-2.5 bg-rose-500/20 rounded-xl text-rose-400 group-hover:bg-rose-500/40 group-hover:text-rose-100 transition-colors ring-1 ring-inset ring-rose-500/30">
                    <MapPinOff className="w-5 h-5" />
                  </div>
                  <div className="text-left">
                    <div className="font-bold text-sm text-rose-50">GPS Spoofing</div>
                    <div className="text-xs text-rose-300/80 font-medium mt-0.5">Test LLM Fraud Filter</div>
                  </div>
                </div>
                <div className="relative z-10 text-rose-500/50 group-hover:text-rose-400 group-hover:translate-x-1 transition-all">
                  <Navigation className="w-4 h-4 rotate-90" />
                </div>
              </button>
            </div>
          </div>
          
          {loading && (
            <div className="mt-6 flex flex-col items-center justify-center py-4 bg-indigo-500/5 rounded-2xl ring-1 ring-inset ring-indigo-500/20">
              <span className="w-5 h-5 border-[3px] border-indigo-500 border-t-transparent rounded-full animate-spin mb-2" />
              <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest text-center">Processing LLM Risk Evaluation</span>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

import React from 'react';

const FeatureCard = ({ icon: Icon, title, description, badge, highlight = false }) => {
  return (
    <div
      className={`cyber-card p-6 relative overflow-hidden transition-all duration-300 ${
        highlight
          ? 'border-cyan-500/40 bg-midnight-900/90 shadow-cyber-sm'
          : 'hover:border-cyan-500/30 hover:bg-midnight-850/80'
      }`}
    >
      {badge && (
        <span className="absolute top-4 right-4 px-2 py-0.5 text-[11px] font-mono font-medium rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">
          {badge}
        </span>
      )}

      <div className="w-12 h-12 rounded-xl bg-midnight-800 border border-slate-700/80 flex items-center justify-center text-cyan-400 mb-5 shadow-sm">
        <Icon className="w-6 h-6 stroke-[2]" />
      </div>

      <h3 className="text-lg font-bold text-white mb-2 tracking-tight">
        {title}
      </h3>

      <p className="text-sm text-slate-400 leading-relaxed">
        {description}
      </p>

      {/* Subtle corner line decor */}
      <div className="absolute bottom-0 right-0 w-8 h-[1px] bg-gradient-to-r from-transparent to-cyan-500/40"></div>
      <div className="absolute bottom-0 right-0 w-[1px] h-8 bg-gradient-to-b from-transparent to-cyan-500/40"></div>
    </div>
  );
};

export default FeatureCard;


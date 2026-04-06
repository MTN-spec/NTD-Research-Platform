'use client';
import { useEffect, useState } from 'react';

interface Node {
  id: string;
  label: string;
  type: string;
  color?: string;
  x?: number;
  y?: number;
}

interface Link {
  source: string;
  target: string;
  label: string;
}

export default function PathwayNetwork() {
  const [data, setData] = useState<{ nodes: Node[]; links: Link[] } | null>(null);

  useEffect(() => {
    fetch('http://localhost:5000/api/pathway')
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) return <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>Loading Biological Architecture...</div>;

  // Simple layout coordinates for a fixed diagram look
  const positions: Record<string, { x: number; y: number }> = {
    'Folate_Cycle': { x: 150, y: 150 },
    'PCP_Pathway': { x: 450, y: 150 },
    'MTHFR': { x: 100, y: 50 },
    'FOLR1': { x: 200, y: 50 },
    'MTHFD1': { x: 150, y: 250 },
    'VANGL2': { x: 400, y: 50 },
    'CELSR1': { x: 500, y: 50 },
    'PAX3': { x: 300, y: 220 },
    'SHH': { x: 450, y: 250 },
  };

  return (
    <div className="glass-card" style={{ height: '400px', position: 'relative', overflow: 'hidden' }}>
      <h3 style={{ marginBottom: '1rem', color: '#3b82f6', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Biomarker Architecture (Bonds)</h3>
      <svg width="100%" height="100%" viewBox="0 0 600 300">
        {/* Draw Links */}
        {data.links.map((link, i) => {
          const s = positions[link.source] || { x: 0, y: 0 };
          const t = positions[link.target] || { x: 0, y: 0 };
          return (
            <g key={i}>
              <line 
                x1={s.x} y1={s.y} x2={t.x} y2={t.y} 
                stroke="rgba(255,255,255,0.1)" strokeWidth="2" strokeDasharray="4 2"
              />
              <text x={(s.x + t.x)/2} y={(s.y + t.y)/2} fill="#64748b" fontSize="8" textAnchor="middle">{link.label}</text>
            </g>
          );
        })}

        {/* Draw Nodes */}
        {data.nodes.map((node) => {
          const pos = positions[node.id] || { x: 0, y: 0 };
          const isProcess = node.type === 'process';
          return (
            <g key={node.id}>
              <circle 
                cx={pos.x} cy={pos.y} r={isProcess ? 25 : 18} 
                fill={isProcess ? (node.color || '#3b82f622') : 'rgba(15, 23, 42, 1)'} 
                stroke={isProcess ? node.color : 'rgba(255,255,255,0.2)'}
                strokeWidth="2"
                style={{ filter: isProcess ? 'drop-shadow(0 0 8px ' + node.color + '44)' : 'none' }}
              />
              <text 
                x={pos.x} y={pos.y + (isProcess ? 40 : 35)} 
                fill="white" fontSize="10" fontWeight="600" textAnchor="middle"
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

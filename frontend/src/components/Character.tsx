import { useId } from "react";
import type { CSSProperties } from "react";

import type { CharacterConfig } from "./character-types";

type CharacterProps = { config: CharacterConfig; emotion?: string; pose?: string; compact?: boolean };

const skin: Record<CharacterConfig["skin_tone"], string> = { porcelain: "#fff0e9", peach: "#f8c4a8", honey: "#e6a36e", almond: "#b9704f", cocoa: "#754634" };
const hair: Record<CharacterConfig["hair_color"], string> = { midnight: "#292642", chestnut: "#68423d", honey: "#d4934d", rose: "#c7597f", lavender: "#8270b2" };
const palette: Record<CharacterConfig["palette"], [string, string]> = { rose: ["#f47ba8", "#d95e9d"], violet: ["#9b87e8", "#7658c4"], mint: ["#69d6bd", "#3aaf9d"], sunset: ["#ffae75", "#e66d66"], night: ["#7074c9", "#414077"] };

export function Character({ config, emotion = "default", pose = "idle", compact = false }: CharacterProps) {
  const [primary, secondary] = palette[config.palette];
  const id = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const isMasculine = config.gender === "masculine";
  const faceRadius = config.head_shape === "round" ? 75 : config.head_shape === "sharp" ? 57 : 67;
  const bodyTransform = pose === "bounce" ? "translateY(-7)" : pose === "tilt" ? "rotate(-4 120 225)" : pose === "victory" ? "translateY(-3)" : "none";
  const eyeY = emotion === "shocked" || emotion === "surprise" ? 148 : 151;
  const eyeScale = emotion === "shocked" ? 1.32 : emotion === "shy" ? .72 : 1;
  const style = { "--character-primary": primary, "--character-secondary": secondary } as CSSProperties;
  const isHappy = ["happy", "love", "proud", "excited"].includes(emotion);
  const isSad = ["sad", "shy"].includes(emotion);
  const hairPath = isMasculine && config.hair_style === "short" ? "M57 119 Q48 72 80 45 Q120 17 160 45 Q192 72 183 119 L158 94 Q120 108 82 94Z" : config.hair_style === "pixie" ? "M57 121 Q50 73 83 50 Q120 28 157 50 Q190 73 183 121 Q160 96 145 90 Q120 104 95 90 Q79 96 57 121Z" : config.hair_style === "side_swept" ? "M47 143 Q36 76 79 49 Q127 20 177 57 Q199 83 184 151 Q160 108 128 91 Q91 76 47 143Z" : config.hair_style === "long" || config.hair_style === "bob" ? "M52 138 Q41 80 80 54 Q120 23 160 54 Q199 80 188 138 Q173 110 162 93 Q120 112 78 93 Q67 110 52 138Z" : config.hair_style === "curly" ? "M53 129 Q32 86 69 52 Q120 19 171 52 Q208 86 187 129 Q169 100 156 91 Q120 106 84 91 Q71 100 53 129Z" : "M54 119 Q48 73 82 53 Q120 31 158 53 Q192 73 186 119 Q166 91 153 86 Q120 100 87 86 Q74 91 54 119Z";

  return <div className={`character character-${pose} ${compact ? "character-compact" : ""}`} style={style} aria-label={`Персонаж Knowly: ${emotion}`}>
    <svg viewBox="0 0 240 300" role="img" aria-hidden="true">
      <defs>
        <linearGradient id={`characterBody-${id}`} x1="0" x2="1" y1="0" y2="1"><stop stopColor="#ffffff" stopOpacity=".18" /><stop offset=".22" stopColor="var(--character-primary)" /><stop offset="1" stopColor="var(--character-secondary)" /></linearGradient>
        <radialGradient id={`characterSkin-${id}`} cx="34%" cy="22%" r="82%"><stop stopColor="#ffffff" stopOpacity=".9" /><stop offset=".15" stopColor={skin[config.skin_tone]} /><stop offset=".72" stopColor={skin[config.skin_tone]} /><stop offset="1" stopColor="#ca7188" /></radialGradient>
        <radialGradient id={`characterHair-${id}`} cx="35%" cy="18%" r="88%"><stop stopColor="#ffffff" stopOpacity=".2" /><stop offset=".25" stopColor={hair[config.hair_color]} /><stop offset="1" stopColor="#25172f" /></radialGradient>
        <filter id={`softShadow-${id}`}><feDropShadow dx="0" dy="9" stdDeviation="8" floodColor="#130d244f" /></filter>
        <filter id={`softGlow-${id}`}><feGaussianBlur stdDeviation="4" /></filter>
      </defs>
      <g transform={bodyTransform} filter={`url(#softShadow-${id})`}>
        <ellipse cx="120" cy="278" rx="62" ry="10" fill="#6c3d7620" />
        <path d={config.outfit === "dress" && !isMasculine ? "M59 276 Q62 210 120 205 Q178 210 181 276Z" : isMasculine ? "M51 276 Q57 206 120 200 Q183 206 189 276Z" : "M68 276 Q69 210 120 205 Q171 210 172 276Z"} fill={`url(#characterBody-${id})`} />
        {isMasculine && <path d="M101 194V222 Q120 235 139 222V194Z" fill={skin[config.skin_tone]} />}
        {config.outfit === "hoodie" && <path d="M87 217 Q120 243 153 217" fill="none" stroke="#ffffff70" strokeWidth="7" />}
        {config.outfit === "jacket" && <><path d="M120 216V276 M93 220L110 236 M147 220L130 236" fill="none" stroke="#ffffff70" strokeWidth="4" /><path d="M94 211 L120 237 L146 211" fill="none" stroke="#ffffff90" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" /></>}
        <path d={isMasculine ? "M78 225 Q53 231 43 260" : "M78 232 Q58 238 50 263"} fill="none" stroke={skin[config.skin_tone]} strokeWidth={isMasculine ? 18 : 16} strokeLinecap="round" />
        <path d={isMasculine ? "M162 225 Q187 231 197 260" : "M162 232 Q182 238 190 263"} fill="none" stroke={skin[config.skin_tone]} strokeWidth={isMasculine ? 18 : 16} strokeLinecap="round" />
        {pose === "victory" && <><path d="M52 255 Q30 236 40 216" fill="none" stroke={skin[config.skin_tone]} strokeWidth="12" strokeLinecap="round" /><path d="M188 255 Q210 236 200 216" fill="none" stroke={skin[config.skin_tone]} strokeWidth="12" strokeLinecap="round" /></>}
        <path d={isMasculine ? `M120 62 C${120 - faceRadius} 72 ${120 - faceRadius - 2} 133 ${120 - 45} 178 L${120 - 36} 199 Q120 226 ${120 + 36} 199 L${120 + 45} 178 C${120 + faceRadius + 2} 133 ${120 + faceRadius} 72 120 62Z` : `M120 ${62 + (config.hair_style === "bun" ? 7 : 0)} C${120 - faceRadius} 78 ${120 - faceRadius - 4} 142 ${120 - faceRadius / 1.1} 184 C${120 - 35} 218 ${120 + 35} 218 ${120 + faceRadius / 1.1} 184 C${120 + faceRadius + 4} 142 ${120 + faceRadius} 78 120 ${62 + (config.hair_style === "bun" ? 7 : 0)}Z`} fill={`url(#characterSkin-${id})`} />
        <path d={hairPath} fill={`url(#characterHair-${id})`} />
        {config.hair_style === "bun" && <circle cx="163" cy="55" r="22" fill={hair[config.hair_color]} />}
        {config.hair_style === "space_buns" && <><circle cx="65" cy="61" r="24" fill={`url(#characterHair-${id})`} /><circle cx="175" cy="61" r="24" fill={`url(#characterHair-${id})`} /></>}
        {config.hat === "beanie" && <><path d="M64 74 Q65 24 120 22 Q175 24 176 74Z" fill={secondary} /><path d="M65 69H175" stroke="#ffffff66" strokeWidth="8" /></>}
        {config.hat === "beret" && <ellipse cx="128" cy="54" rx="63" ry="25" fill={secondary} transform="rotate(-8 128 54)" />}
        {config.hat === "halo" && <ellipse cx="120" cy="24" rx="48" ry="12" fill="none" stroke="#ffd76d" strokeWidth="7" />}
        {config.accessory === "headphones" && <><path d="M54 134V116 Q54 51 120 51 Q186 51 186 116V134" fill="none" stroke="#ff79b1" strokeWidth="9" strokeLinecap="round" /><rect x="46" y="120" width="18" height="34" rx="8" fill="#9b87e8" /><rect x="176" y="120" width="18" height="34" rx="8" fill="#9b87e8" /></>}
        {config.accessory === "crown" && <path d="M82 65L91 36L120 55L149 36L158 65Z" fill="#ffd76d" stroke="#fff2b0" strokeWidth="3" />}
        {config.accessory === "bow" && <><path d="M177 109 Q204 91 207 114 Q204 137 177 122Z" fill="#ff6d9f" /><path d="M177 109 Q150 91 147 114 Q150 137 177 122Z" fill="#ff94bd" /><circle cx="177" cy="116" r="7" fill="#ffd76d" /></>}
        <path d={config.brows === "arched" ? "M78 133 Q91 122 102 133 M138 133 Q149 122 162 133" : config.brows === "straight" || isMasculine ? "M78 130H102 M138 130H162" : "M78 132 Q90 126 102 132 M138 132 Q150 126 162 132"} fill="none" stroke="#583b48" strokeWidth={config.brows === "bold" || isMasculine ? 6 : 4} strokeLinecap="round" />
        <path d="M76 113 Q111 89 151 104" fill="none" stroke="#ffffff55" strokeWidth="6" strokeLinecap="round" filter={`url(#softGlow-${id})`} />
        <g transform={`translate(0 ${eyeY - 151}) scale(1 ${eyeScale})`}>
          {config.eyes === "sparkle" ? <><circle cx="91" cy="151" r="10" fill="#25152f" /><circle cx="149" cy="151" r="10" fill="#25152f" /><circle cx="87" cy="146" r="4" fill="white" /><circle cx="145" cy="146" r="4" fill="white" /><circle cx="95" cy="157" r="2" fill="#ffffff88" /><circle cx="153" cy="157" r="2" fill="#ffffff88" /></> : config.eyes === "mischief" ? <><path d="M79 151 Q91 140 103 151" fill="none" stroke="#25152f" strokeWidth="5" /><path d="M137 151 Q149 140 161 151" fill="none" stroke="#25152f" strokeWidth="5" /></> : <><ellipse cx="91" cy="151" rx={config.eyes === "round" ? 10 : 8} ry="11" fill="#25152f" /><ellipse cx="149" cy="151" rx={config.eyes === "round" ? 10 : 8} ry="11" fill="#25152f" /><circle cx="88" cy="147" r="4" fill="white" /><circle cx="146" cy="147" r="4" fill="white" /><circle cx="95" cy="157" r="2" fill="#ffffff88" /><circle cx="153" cy="157" r="2" fill="#ffffff88" /></>}
        </g>
        {config.glasses !== "none" && <><circle cx="90" cy="151" r="20" fill="none" stroke="#47384f" strokeWidth="4" /><circle cx="150" cy="151" r="20" fill="none" stroke="#47384f" strokeWidth="4" /><path d="M110 151H130" stroke="#47384f" strokeWidth="4" /></>}
        {isHappy ? <path d={isMasculine ? "M104 175 Q120 184 136 175" : "M105 174 Q120 188 135 174"} fill="none" stroke="#ac4865" strokeWidth="5" strokeLinecap="round" /> : isSad ? <path d="M106 184 Q120 171 134 184" fill="none" stroke="#ac4865" strokeWidth="5" strokeLinecap="round" /> : <path d="M109 177 Q120 181 131 177" fill="none" stroke="#ac4865" strokeWidth="4" strokeLinecap="round" />}
        <ellipse cx="82" cy="174" rx="12" ry="6" fill="#ff8da8" opacity=".3" filter={`url(#softGlow-${id})`} />
        <ellipse cx="158" cy="174" rx="12" ry="6" fill="#ff8da8" opacity=".3" filter={`url(#softGlow-${id})`} />
        {emotion === "shy" && <path d="M70 172 Q80 166 90 172 M150 172 Q160 166 170 172" stroke="#e88991" strokeWidth="7" strokeLinecap="round" opacity=".7" />}
        {config.accessory === "heart" && <text x="177" y="113" fill="#f36b9e" fontSize="25">♥</text>}
        {config.accessory === "star" && <text x="177" y="113" fill="#ffd15c" fontSize="26">✦</text>}
        {config.accessory === "flower" && <text x="176" y="113" fill="#ff96b7" fontSize="23">✿</text>}
        {config.accessory === "sparkle" && <text x="177" y="113" fill="#b69bff" fontSize="25">✧</text>}
        {config.accessory === "scarf" && <path d="M78 213 Q120 228 162 213L158 235 Q120 248 82 235Z" fill="#ff6d9f" stroke="#ffb1d0" strokeWidth="3" />}
        {config.accessory === "earrings" && <><circle cx="64" cy="181" r="6" fill="#ffd76d" /><circle cx="176" cy="181" r="6" fill="#ffd76d" /></>}
        {emotion === "excited" && <g fill="#f3a2c4"><circle cx="40" cy="102" r="4" /><circle cx="197" cy="174" r="4" /><circle cx="45" cy="190" r="3" /></g>}
      </g>
    </svg>
  </div>;
}

export const defaultCharacter: CharacterConfig = {
  gender: "feminine", personality: "romantic", head_shape: "soft", skin_tone: "peach", hair_style: "bob", hair_color: "chestnut", eyes: "soft", brows: "soft", outfit: "sweater", accessory: "heart", glasses: "none", hat: "none", palette: "rose",
};

export const masculineCharacter: CharacterConfig = {
  gender: "masculine", personality: "confident", head_shape: "sharp", skin_tone: "honey", hair_style: "short", hair_color: "midnight", eyes: "mischief", brows: "bold", outfit: "jacket", accessory: "none", glasses: "none", hat: "none", palette: "night",
};

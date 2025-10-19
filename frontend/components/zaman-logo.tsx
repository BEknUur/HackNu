import React from 'react';
import Svg, { Path, G, Defs, LinearGradient, Stop } from 'react-native-svg';
import { ZamanColors } from '@/constants/theme';

interface ZamanLogoProps {
  size?: number;
  withAccent?: boolean;
}

export default function ZamanLogo({ size = 80, withAccent = true }: ZamanLogoProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 240 280" fill="none">
      <Defs>
        <LinearGradient id="solarGlow" x1="0%" y1="0%" x2="100%" y2="100%">
          <Stop offset="0%" stopColor={ZamanColors.solar} stopOpacity="0.6" />
          <Stop offset="100%" stopColor={ZamanColors.solar} stopOpacity="0.2" />
        </LinearGradient>
      </Defs>
      <G>
        {/* Top left square */}
        <Path
          d="M70 45 L125 45 L125 100 L70 100 Z"
          stroke={ZamanColors.persianGreen}
          strokeWidth="7"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        
        {/* Top right rotated square (diamond) - with solar accent */}
        <Path
          d="M165 35 L205 75 L165 115 L125 75 Z"
          stroke={withAccent ? ZamanColors.solar : ZamanColors.persianGreen}
          strokeWidth="7"
          fill={withAccent ? "url(#solarGlow)" : "none"}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        
        {/* Middle left rotated square (diamond) */}
        <Path
          d="M35 115 L75 155 L35 195 L-5 155 Z"
          stroke={ZamanColors.persianGreen}
          strokeWidth="7"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        
        {/* Middle center square - with solar accent on border */}
        <Path
          d="M95 125 L145 125 L145 175 L95 175 Z"
          stroke={ZamanColors.persianGreen}
          strokeWidth="7"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {withAccent && (
          <Path
            d="M95 125 L145 125"
            stroke={ZamanColors.solar}
            strokeWidth="8"
            strokeLinecap="round"
          />
        )}
        
        {/* Bottom right rotated square (diamond) */}
        <Path
          d="M185 195 L225 235 L185 275 L145 235 Z"
          stroke={ZamanColors.persianGreen}
          strokeWidth="7"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        
        {/* Connecting lines for geometric effect */}
        <Path
          d="M97 72 L125 100 M165 115 L120 150"
          stroke={ZamanColors.persianGreen}
          strokeWidth="5"
          strokeLinecap="round"
          opacity="0.7"
        />
      </G>
    </Svg>
  );
}


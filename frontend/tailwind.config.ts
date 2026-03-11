import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
  	container: {
  		center: true,
  		padding: '2rem',
  		screens: {
  			'2xl': '1400px'
  		}
  	},
  	extend: {
  		colors: {
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			},
  			success: {
  				DEFAULT: 'hsl(142 76% 36%)',
  				foreground: 'hsl(0 0% 100%)',
  				light: 'hsl(142 76% 96%)'
  			},
  			warning: {
  				DEFAULT: 'hsl(38 92% 50%)',
  				foreground: 'hsl(0 0% 100%)',
  				light: 'hsl(38 92% 96%)'
  			},
  			danger: {
  				DEFAULT: 'hsl(0 84% 60%)',
  				foreground: 'hsl(0 0% 100%)',
  				light: 'hsl(0 84% 96%)'
  			},
  			info: {
  				DEFAULT: 'hsl(217 91% 60%)',
  				foreground: 'hsl(0 0% 100%)',
  				light: 'hsl(217 91% 96%)'
  			}
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			},
  			'fade-in': {
  				from: {
  					opacity: '0'
  				},
  				to: {
  					opacity: '1'
  				}
  			},
  			'slide-up': {
  				from: {
  					transform: 'translateY(10px)',
  					opacity: '0'
  				},
  				to: {
  					transform: 'translateY(0)',
  					opacity: '1'
  				}
  			},
      		shimmer: {
      				'0%': {
      					backgroundPosition: '-1000px 0'
      				},
      				'100%': {
      					backgroundPosition: '1000px 0'
      				}
      			},
      			pulse: {
      				'0%, 100%': {
      					opacity: '1'
      				},
      				'50%': {
      					opacity: '0.5'
      				}
      			},
      			blob: {
      				'0%': {
      					transform: 'translate(0px, 0px) scale(1)'
      				},
      				'33%': {
      					transform: 'translate(30px, -50px) scale(1.1)'
      				},
      				'66%': {
      					transform: 'translate(-20px, 20px) scale(0.9)'
      				},
      				'100%': {
      					transform: 'translate(0px, 0px) scale(1)'
      				}
      			},
      			float: {
      				'0%, 100%': {
      					transform: 'translateY(0px)'
      				},
      				'50%': {
      					transform: 'translateY(-20px)'
      				}
      			},
      			glow: {
      				'0%, 100%': {
      					opacity: '1',
      					boxShadow: '0 0 20px rgb(59 130 246 / 0.5)'
      				},
      				'50%': {
      					opacity: '0.8',
      					boxShadow: '0 0 30px rgb(59 130 246 / 0.8)'
      				}
      			}
      		},
      		animation: {
      			'accordion-down': 'accordion-down 0.2s ease-out',
      			'accordion-up': 'accordion-up 0.2s ease-out',
      			'fade-in': 'fade-in 0.3s ease-out',
      			'slide-up': 'slide-up 0.3s ease-out',
      			shimmer: 'shimmer 2s linear infinite',
      			pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      			blob: 'blob 7s infinite',
      			float: 'float 3s ease-in-out infinite',
      			glow: 'glow 2s ease-in-out infinite'
      		},
      		animationDelay: {
      			'2000': '2s',
      			'4000': '4s'
      		},
  		boxShadow: {
  			soft: '0 2px 8px rgba(0, 0, 0, 0.08)',
  			medium: '0 4px 12px rgba(0, 0, 0, 0.12)',
  			large: '0 8px 24px rgba(0, 0, 0, 0.16)'
  		}
  	}
  },
  plugins: [
    require("tailwindcss-animate"),
    require("@tailwindcss/typography")
  ],
};
export default config;

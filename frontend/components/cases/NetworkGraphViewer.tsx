'use client'

import React, { useRef, useEffect, useState, useMemo } from 'react'
import dynamic from 'next/dynamic'

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false })
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card'
import { Badge } from '../ui/badge'
import { Network, ZoomIn, ZoomOut, Maximize, AlertCircle } from 'lucide-react'
import { NetworkGraphData, NetworkNode } from '@/types'

// Type coercion for react-force-graph
type ForceGraphNode = {
	id: string
	val: number
	color: string
	name: string
	label: string
	x?: number
	y?: number
	vx?: number
	vy?: number
}

interface NetworkGraphViewerProps {
	data: NetworkGraphData | null
	isLoading?: boolean
}

export function NetworkGraphViewer({ data, isLoading }: NetworkGraphViewerProps) {
	const containerRef = useRef<HTMLDivElement>(null)
	const [dimensions, setDimensions] = useState({ width: 600, height: 400 })
	const graphRef = useRef<any>(null)

	useEffect(() => {
		const updateDimensions = () => {
			if (containerRef.current) {
				setDimensions({
					width: containerRef.current.offsetWidth,
					height: containerRef.current.offsetHeight || 400
				})
			}
		}

		// Initial size
		updateDimensions()

		window.addEventListener('resize', updateDimensions)
		return () => window.removeEventListener('resize', updateDimensions)
	}, [])

	const handleZoomIn = () => {
		if (graphRef.current) {
			const currentZoom = graphRef.current.zoom()
			graphRef.current.zoom(currentZoom * 1.5, 300)
		}
	}

	const handleZoomOut = () => {
		if (graphRef.current) {
			const currentZoom = graphRef.current.zoom()
			graphRef.current.zoom(currentZoom / 1.5, 300)
		}
	}

	const handleFit = () => {
		if (graphRef.current) {
			graphRef.current.zoomToFit(400, 20)
		}
	}

	const graphData = useMemo(() => {
		if (!data) return { nodes: [], links: [] }

		const nodes: ForceGraphNode[] = data.nodes.map(n => {
			let color = '#ccc'
			let val = 4
			if (n.type === 'CUSTOMER') color = '#3b82f6'
			if (n.type === 'PAYEE') color = '#10b981'
			if (n.type === 'ACCOUNT') color = '#6366f1'
			if (n.type === 'MULE') {
				color = '#ef4444'
				val = 8
			}

			return {
				id: n.id,
				name: n.label,
				label: n.label,
				color,
				val
			}
		})

		const links = data.edges.map(e => ({
			source: e.source,
			target: e.target,
			name: e.type,
			color: e.type === 'TRANSACTION' ? '#10b981' : '#ccc'
		}))

		return { nodes, links }
	}, [data])

	return (
		<Card className="h-[500px] flex flex-col relative overflow-hidden bg-neutral-50 dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800">
			<CardHeader className="pb-2 border-b bg-white dark:bg-neutral-950 z-10 flex flex-row items-center justify-between">
				<div>
					<CardTitle className="text-md flex items-center">
						<Network className="w-5 h-5 mr-2 text-indigo-500" />
						Graph Intelligence
					</CardTitle>
					<CardDescription>2nd-degree entity relationships</CardDescription>
				</div>
				<div className="flex space-x-2">
					<button onClick={handleZoomIn} className="p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-md">
						<ZoomIn className="w-4 h-4 text-neutral-500" />
					</button>
					<button onClick={handleZoomOut} className="p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-md">
						<ZoomOut className="w-4 h-4 text-neutral-500" />
					</button>
					<button onClick={handleFit} className="p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-md">
						<Maximize className="w-4 h-4 text-neutral-500" />
					</button>
				</div>
			</CardHeader>
			<CardContent className="flex-1 p-0 relative" ref={containerRef}>
				{isLoading ? (
					<div className="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-black/50 backdrop-blur-sm z-20">
						<div className="flex flex-col items-center">
							<div className="w-8 h-8 rounded-full border-t-2 border-indigo-500 spin animate-spin mb-2" />
							<span className="text-sm font-medium text-indigo-500">Processing Topology...</span>
						</div>
					</div>
				) : !data || data.nodes.length === 0 ? (
					<div className="absolute inset-0 flex items-center justify-center text-neutral-400 flex-col">
						<AlertCircle className="w-8 h-8 mb-2 opacity-50" />
						<p>No network data available for this entity.</p>
					</div>
				) : (
					<ForceGraph2D
						ref={graphRef}
						width={dimensions.width}
						height={dimensions.height}
						graphData={graphData}
						nodeLabel="name"
						nodeColor="color"
						nodeVal="val"
						linkColor="color"
						linkWidth={2}
						linkDirectionalArrowLength={3.5}
						linkDirectionalArrowRelPos={1}
						onNodeClick={(node, event) => {
							if (graphRef.current) {
								graphRef.current.centerAt(node.x, node.y, 1000)
								graphRef.current.zoom(8, 2000)
							}
						}}
					/>
				)}

				{/* Legend */}
				{data && data.nodes.length > 0 && (
					<div className="absolute bottom-4 left-4 bg-white/90 dark:bg-neutral-950/90 backdrop-blur-md p-3 rounded-lg border shadow-sm text-xs font-medium space-y-2 pointer-events-none z-10">
						<div className="flex items-center"><span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span> Customer</div>
						<div className="flex items-center"><span className="w-3 h-3 bg-emerald-500 rounded-full mr-2"></span> Payee</div>
						<div className="flex items-center"><span className="w-3 h-3 bg-indigo-500 rounded-full mr-2"></span> Account</div>
						<div className="flex items-center"><span className="w-3 h-3 bg-red-500 rounded-full mr-2"></span> Known Mule</div>
					</div>
				)}
			</CardContent>
		</Card>
	)
}

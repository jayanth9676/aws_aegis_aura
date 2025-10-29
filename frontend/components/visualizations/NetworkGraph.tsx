'use client'

import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import type { NetworkGraphData, NetworkNode, NetworkEdge } from '@/types'
import { Button } from '@/components/ui/button'
import { ZoomIn, ZoomOut, Maximize } from 'lucide-react'

interface NetworkGraphProps {
  data: NetworkGraphData
}

export function NetworkGraph({ data }: NetworkGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || !data) return

    const width = containerRef.current.clientWidth
    const height = 500

    // Clear existing content
    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3
      .select(svgRef.current)
      .attr('width', width)
      .attr('height', height)

    const g = svg.append('g')

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom as any)

    // Create force simulation
    const simulation = d3
      .forceSimulation(data.nodes as any)
      .force('link', d3.forceLink(data.edges).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40))

    // Create edges
    const link = g
      .append('g')
      .selectAll('line')
      .data(data.edges)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d: NetworkEdge) => d.amount ? Math.sqrt(d.amount / 1000) : 2)

    // Create nodes
    const node = g
      .append('g')
      .selectAll('circle')
      .data(data.nodes)
      .enter()
      .append('circle')
      .attr('r', 20)
      .attr('fill', (d: NetworkNode) => {
        switch (d.type) {
          case 'CUSTOMER':
            return '#3b82f6'
          case 'PAYEE':
            return '#10b981'
          case 'MULE':
            return '#ef4444'
          default:
            return '#8b5cf6'
        }
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .call(d3.drag<any, any>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any)

    // Add labels
    const labels = g
      .append('g')
      .selectAll('text')
      .data(data.nodes)
      .enter()
      .append('text')
      .text((d: NetworkNode) => d.label)
      .attr('font-size', 12)
      .attr('dx', 25)
      .attr('dy', 5)
      .style('pointer-events', 'none')

    // Add tooltips
    const tooltip = d3
      .select(containerRef.current)
      .append('div')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background-color', 'hsl(var(--background))')
      .style('border', '1px solid hsl(var(--border))')
      .style('border-radius', '6px')
      .style('padding', '8px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000')

    node.on('mouseover', function (event, d: NetworkNode) {
      tooltip
        .html(`
          <strong>${d.label}</strong><br/>
          Type: ${d.type}<br/>
          ${d.risk_score ? `Risk Score: ${d.risk_score}` : ''}
        `)
        .style('visibility', 'visible')
    })
      .on('mousemove', function (event) {
        tooltip
          .style('top', event.pageY - 10 + 'px')
          .style('left', event.pageX + 10 + 'px')
      })
      .on('mouseout', function () {
        tooltip.style('visibility', 'hidden')
      })

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      node.attr('cx', (d: any) => d.x).attr('cy', (d: any) => d.y)

      labels.attr('x', (d: any) => d.x).attr('y', (d: any) => d.y)
    })

    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    }

    function dragged(event: any) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0)
      event.subject.fx = null
      event.subject.fy = null
    }

    return () => {
      simulation.stop()
      tooltip.remove()
    }
  }, [data])

  return (
    <div ref={containerRef} className="relative w-full">
      <svg ref={svgRef} className="border rounded-lg bg-muted/30" />
      
      {/* Legend */}
      <div className="absolute top-4 right-4 bg-background/95 border rounded-lg p-3 text-xs space-y-2">
        <div className="font-semibold mb-2">Node Types</div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span>Customer</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span>Payee</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span>Mule Account</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-purple-500" />
          <span>Account</span>
        </div>
      </div>

      {/* Controls */}
      <div className="absolute bottom-4 left-4 flex gap-2">
        <Button variant="outline" size="icon" onClick={() => {
          const svg = d3.select(svgRef.current!)
          const zoom = d3.zoom<SVGSVGElement, unknown>()
          svg.transition().call(zoom.scaleBy as any, 1.2)
        }}>
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="icon" onClick={() => {
          const svg = d3.select(svgRef.current!)
          const zoom = d3.zoom<SVGSVGElement, unknown>()
          svg.transition().call(zoom.scaleBy as any, 0.8)
        }}>
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="icon" onClick={() => {
          const svg = d3.select(svgRef.current!)
          const zoom = d3.zoom<SVGSVGElement, unknown>()
          svg.transition().call(zoom.transform as any, d3.zoomIdentity)
        }}>
          <Maximize className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

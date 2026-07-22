#!/usr/bin/env python3
"""Reusable D3 multi-graph tour helpers for the pr-walkthrough skill."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from textwrap import dedent

D3_VERSION = "7.9.0"
D3_CDN_URL = f"https://cdn.jsdelivr.net/npm/d3@{D3_VERSION}/dist/d3.min.js"


def d3_canvas_css() -> str:
    return dedent(
        """
        :root {
          --warp-bg: #121212;
          --warp-panel: #1e1e1d;
          --warp-panel-2: #292929;
          --warp-border: #404040;
          --warp-text: #faf9f6;
          --warp-muted: #b4b4b2;
          --warp-dim: #868584;
          --warp-accent: #a43787;
          --warp-green: #34895c;
          --warp-blue: #2e5d9e;
          --warp-purple: #754dac;
          --warp-yellow: #c0872a;
          --warp-font-sans: 'Matter', 'DM Sans', system-ui, sans-serif;
          --warp-font-mono: 'Matter Mono', 'Roboto Mono', ui-monospace, monospace;
        }
        * { box-sizing: border-box; }
        body { margin: 0; min-height: 100vh; background: var(--warp-bg); color: var(--warp-text); font-family: var(--warp-font-sans); }
        a { color: var(--warp-text); text-decoration-color: var(--warp-accent); text-underline-offset: 3px; }
        button, input { font: inherit; }
        .d3-walkthrough-shell { min-height: 100vh; display: grid; grid-template-rows: auto 1fr; }
        .d3-walkthrough-header { display: grid; gap: 10px; padding: 28px 32px 20px; border-bottom: 1px solid var(--warp-border); background: linear-gradient(180deg, #1e1e1d, #121212); }
        .d3-kicker { color: var(--warp-accent); font-family: var(--warp-font-mono); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; }
        .d3-walkthrough-header h1 { margin: 0; max-width: 1080px; font-size: clamp(34px, 5vw, 72px); line-height: 0.95; letter-spacing: -0.04em; }
        .d3-meta-row { display: flex; flex-wrap: wrap; gap: 8px; color: var(--warp-muted); font-family: var(--warp-font-mono); font-size: 12px; }
        .d3-summary { max-width: 920px; margin: 0; color: var(--warp-muted); font-size: 17px; line-height: 1.45; }
        .d3-canvas-layout { min-height: 0; display: grid; grid-template-columns: 310px minmax(560px, 1fr) 390px; gap: 0; }
        .d3-control-panel, .d3-detail-panel { min-height: 0; overflow: auto; background: var(--warp-panel); border-right: 1px solid var(--warp-border); padding: 18px; }
        .d3-detail-panel { border-right: 0; border-left: 1px solid var(--warp-border); }
        .d3-panel-title { margin: 0 0 12px; font-size: 12px; color: var(--warp-muted); font-family: var(--warp-font-mono); letter-spacing: 0.08em; text-transform: uppercase; }
        .d3-control-stack { display: grid; gap: 10px; margin-bottom: 18px; }
        .d3-control-button, .d3-graph-toggle { border: 1px solid var(--warp-border); background: var(--warp-panel-2); color: var(--warp-text); border-radius: 10px; padding: 10px 12px; cursor: pointer; text-align: left; }
        .d3-control-button:hover, .d3-graph-toggle:hover, .d3-control-button:focus, .d3-graph-toggle:focus { border-color: var(--warp-accent); outline: none; }
        .d3-graph-toggle[aria-pressed="true"] { border-color: var(--graph-color, var(--warp-accent)); box-shadow: inset 3px 0 0 var(--graph-color, var(--warp-accent)); }
        .d3-tour-card { border: 1px solid var(--warp-border); background: #121212; border-radius: 12px; padding: 12px; margin-bottom: 14px; }
        .d3-tour-step-label { color: var(--warp-accent); font-family: var(--warp-font-mono); font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; }
        .d3-tour-title { margin: 6px 0; font-size: 18px; line-height: 1.15; }
        .d3-tour-body { color: var(--warp-muted); line-height: 1.4; margin: 0; }
        .d3-search { width: 100%; border: 1px solid var(--warp-border); background: #121212; color: var(--warp-text); border-radius: 10px; padding: 10px 12px; }
        .d3-search:focus { border-color: var(--warp-accent); outline: none; }
        .d3-help { color: var(--warp-dim); font-family: var(--warp-font-mono); font-size: 11px; line-height: 1.5; }
        .d3-canvas-stage { min-height: 0; position: relative; overflow: hidden; background: radial-gradient(circle at 20% 20%, #a4378722, transparent 28%), radial-gradient(circle at 80% 70%, #2e5d9e22, transparent 26%), #121212; }
        #pr-walkthrough-canvas { width: 100%; height: 100%; min-height: 700px; display: block; }
        .d3-canvas-error { position: absolute; inset: 18px; display: none; place-items: center; border: 1px solid var(--warp-border); background: #1e1e1df2; color: var(--warp-text); padding: 24px; z-index: 2; }
        body.d3-canvas-error .d3-canvas-error { display: grid; }
        .d3-graph-title { fill: #faf9f6; opacity: 0.36; font-family: var(--warp-font-mono); font-size: 13px; letter-spacing: 0.08em; text-transform: uppercase; }
        .d3-edge path { fill: none; stroke: var(--edge-color, #868584); stroke-width: 2; stroke-opacity: 0.68; }
        .d3-edge-arrow path { fill: var(--edge-color, #868584); }
        .d3-edge text { fill: #cccbc8; font-family: var(--warp-font-mono); font-size: 11px; paint-order: stroke; stroke: #121212; stroke-width: 4px; stroke-linejoin: round; }
        .d3-node { cursor: pointer; }
        .d3-node rect { fill: #1e1e1d; stroke: var(--node-color, var(--warp-accent)); stroke-width: 2; filter: drop-shadow(0 10px 24px #00000066); }
        .d3-node.is-selected rect { stroke: var(--warp-accent); stroke-width: 4; }
        .d3-node.is-tour-node rect { stroke: var(--warp-accent); stroke-width: 4; filter: drop-shadow(0 0 18px #a4378788); }
        .d3-node.is-dimmed, .d3-edge.is-dimmed { opacity: 0.18; }
        .d3-node-title { fill: #faf9f6; font-family: var(--warp-font-sans); font-size: 15px; font-weight: 700; pointer-events: none; }
        .d3-node-kind { fill: #b4b4b2; font-family: var(--warp-font-mono); font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; pointer-events: none; }
        .d3-node-summary { fill: #cccbc8; font-family: var(--warp-font-sans); font-size: 12px; pointer-events: none; }
        .d3-detail-title { margin: 0 0 6px; font-size: 24px; line-height: 1.1; }
        .d3-detail-kind { color: var(--warp-accent); font-family: var(--warp-font-mono); font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; }
        .d3-detail-summary { color: var(--warp-muted); line-height: 1.45; }
        .d3-detail-section { margin-top: 18px; }
        .d3-detail-section h3 { margin: 0 0 8px; color: var(--warp-muted); font-family: var(--warp-font-mono); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; }
        .d3-detail-list { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; }
        .d3-detail-list li { border: 1px solid var(--warp-border); background: #121212; border-radius: 10px; padding: 10px; color: var(--warp-muted); line-height: 1.35; }
        .d3-file-link { display: block; overflow-wrap: anywhere; color: var(--warp-text); font-family: var(--warp-font-mono); font-size: 12px; }
        .d3-comment-author { display: block; color: var(--warp-accent); font-family: var(--warp-font-mono); font-size: 11px; margin-bottom: 4px; }
        .d3-empty { color: var(--warp-dim); }
        @media (max-width: 1180px) { .d3-canvas-layout { grid-template-columns: 1fr; grid-template-rows: auto minmax(680px, 1fr) auto; } .d3-control-panel, .d3-detail-panel { border: 0; border-bottom: 1px solid var(--warp-border); max-height: 360px; } }
        """
    ).strip()


def d3_canvas_runtime_script() -> str:
    return dedent(
        f"""
        <script>
        (() => {{
          const D3_CDN_URL = {D3_CDN_URL!r};
          let attemptedLoad = false;
          let activeGraphId = null;
          let selectedNodeId = null;
          let tourIndex = 0;
          const REQUIRED_GRAPH_IDS = ['system-overview', 'data-flow', 'code-dependency', 'user-action'];
          const DEFAULT_NODE_WIDTH = 220;
          const DEFAULT_NODE_HEIGHT = 116;
          const OVERVIEW_NODE_WIDTH = 360;
          const OVERVIEW_NODE_HEIGHT = 220;
          let zoomBehavior = null;
          let svgSelection = null;
          let viewportSelection = null;
          let currentData = null;

          function setError(error) {{
            console.warn('D3 canvas render unavailable.', error || 'unknown error');
            document.body.classList.add('d3-canvas-error');
            const errorNode = document.querySelector('.d3-canvas-error');
            if (errorNode) errorNode.textContent = `D3 canvas failed to render: ${{error?.message || error || 'unknown error'}}`;
          }}

          function readInlineData() {{
            if (window.PR_WALKTHROUGH_D3_DATA) return window.PR_WALKTHROUGH_D3_DATA;
            const script = document.getElementById('pr-walkthrough-data');
            if (!script) throw new Error('Missing pr-walkthrough-data script tag');
            return JSON.parse(script.textContent || '{{}}');
          }}

          function activeGraph() {{
            return (currentData.graphs || []).find((graph) => graph.id === activeGraphId) || (currentData.graphs || [])[0];
          }}

          function nodeMap(graph) {{ return new Map((graph.nodes || []).map((node) => [node.id, node])); }}
          function escapeHtml(value) {{
            return String(value ?? '').replace(/[&<>"']/g, (char) => ({{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }}[char]));
          }}
          function listItems(items, render) {{
            if (!items || items.length === 0) return '<p class="d3-empty">None attached.</p>';
            return `<ul class="d3-detail-list">${{items.map(render).join('')}}</ul>`;
          }}

          function renderTour(graph) {{
            const step = (graph.tour || [])[tourIndex];
            const label = document.querySelector('.d3-tour-step-label');
            const title = document.querySelector('.d3-tour-title');
            const body = document.querySelector('.d3-tour-body');
            const card = document.querySelector('.d3-tour-card');
            if (card) card.dataset.tourIndex = String(tourIndex);
            if (label) label.textContent = `Step ${{Math.min(tourIndex + 1, (graph.tour || []).length)}} / ${{(graph.tour || []).length || 0}}`;
            if (title) title.textContent = step?.title || graph.label || 'View tour';
            if (body) body.textContent = step?.body || graph.summary || '';
          }}

          function renderDetails(node, graph) {{
            const panel = document.getElementById('pr-walkthrough-details');
            if (!panel) return;
            const step = (graph.tour || [])[tourIndex];
            if (!node) {{
              panel.innerHTML = '<p class="d3-panel-title">Selected point</p><p class="d3-empty">Select a node or use the tour controls.</p>';
              return;
            }}
            const details = Array.isArray(node.details) ? node.details : [];
            const files = Array.isArray(node.files) ? node.files : [];
            const comments = Array.isArray(node.comments) ? node.comments : [];
            const links = Array.isArray(node.links) ? node.links : [];
            panel.innerHTML = `
              <span class="d3-detail-kind">${{escapeHtml(graph.label)}} · ${{escapeHtml(node.kind || 'point of interest')}}</span>
              <h2 class="d3-detail-title">${{escapeHtml(node.title)}}</h2>
              <p class="d3-detail-summary">${{escapeHtml(node.summary || '')}}</p>
              ${{step?.nodeId === node.id ? `<section class="d3-detail-section"><h3>Tour context</h3><ul class="d3-detail-list"><li>${{escapeHtml(step.body || '')}}</li></ul></section>` : ''}}
              <section class="d3-detail-section"><h3>Explanation</h3>${{details.length ? `<ul class="d3-detail-list">${{details.map((item) => `<li>${{escapeHtml(item)}}</li>`).join('')}}</ul>` : '<p class="d3-empty">No additional detail provided.</p>'}}</section>
              <section class="d3-detail-section"><h3>Changed files</h3>${{listItems(files, (file) => `<li><a class="d3-file-link" href="${{escapeHtml(file.url || '#')}}" target="_blank" rel="noreferrer">${{escapeHtml(file.path || file.label || 'file')}}</a>${{file.note ? `<p>${{escapeHtml(file.note)}}</p>` : ''}}</li>`)}}</section>
              <section class="d3-detail-section"><h3>Existing review discussion</h3>${{listItems(comments, (comment) => `<li><span class="d3-comment-author">${{escapeHtml(comment.author || 'reviewer')}}</span>${{escapeHtml(comment.body || '')}}${{comment.url ? `<br><a href="${{escapeHtml(comment.url)}}" target="_blank" rel="noreferrer">Open comment</a>` : ''}}</li>`)}}</section>
              <section class="d3-detail-section"><h3>Links</h3>${{listItems(links, (link) => `<li><a href="${{escapeHtml(link.url || '#')}}" target="_blank" rel="noreferrer">${{escapeHtml(link.label || link.url || 'link')}}</a></li>`)}}</section>
            `;
          }}

          function wrapText(selection, width, maxLines = 3) {{
            selection.each(function wrapEach() {{
              const text = window.d3.select(this);
              const datum = text.datum();
              const resolvedWidth = typeof width === 'function' ? Number(width(datum)) : Number(width);
              const resolvedMaxLines = typeof maxLines === 'function' ? Number(maxLines(datum)) : Number(maxLines);
              const words = text.text().split(new RegExp('\\\\s+')).filter(Boolean);
              const lineHeight = 15;
              const y = Number(text.attr('y') || 0);
              text.text('');
              let line = [];
              let lineNumber = 0;
              let tspan = text.append('tspan').attr('x', text.attr('x')).attr('y', y);
              for (const word of words) {{
                line.push(word);
                tspan.text(line.join(' '));
                if (tspan.node().getComputedTextLength() > resolvedWidth && line.length > 1) {{
                  line.pop();
                  tspan.text(line.join(' '));
                  line = [word];
                  lineNumber += 1;
                  if (lineNumber >= resolvedMaxLines) {{ tspan.text(`${{tspan.text()}}…`); break; }}
                  tspan = text.append('tspan').attr('x', text.attr('x')).attr('y', y + lineNumber * lineHeight).text(word);
                }}
              }}
            }});
          }}
          function nodeWidth(node, graph) {{
            return Number(node.width || (graph?.id === 'system-overview' ? OVERVIEW_NODE_WIDTH : DEFAULT_NODE_WIDTH));
          }}
          function nodeHeight(node, graph) {{
            return Number(node.height || (graph?.id === 'system-overview' ? OVERVIEW_NODE_HEIGHT : DEFAULT_NODE_HEIGHT));
          }}
          function nodeBoundaryPoint(from, to, padding, graph) {{
            const dx = to.x - from.x;
            const dy = to.y - from.y;
            if (dx === 0 && dy === 0) return {{ x: from.x, y: from.y }};
            const scale = 1 / Math.max(Math.abs(dx) / (nodeWidth(from, graph) / 2 + padding), Math.abs(dy) / (nodeHeight(from, graph) / 2 + padding));
            return {{ x: from.x + dx * scale, y: from.y + dy * scale }};
          }}
          function pathForEdge(edge, nodes, graph) {{
            const source = nodes.get(edge.source);
            const target = nodes.get(edge.target);
            if (!source || !target) return '';
            const start = nodeBoundaryPoint(source, target, 10, graph);
            const end = nodeBoundaryPoint(target, source, 18, graph);
            const dx = end.x - start.x;
            const control = Math.max(80, Math.abs(dx) * 0.42);
            return `M ${{start.x}} ${{start.y}} C ${{start.x + control}} ${{start.y}}, ${{end.x - control}} ${{end.y}}, ${{end.x}} ${{end.y}}`;
          }}

          function applyFilters(graph) {{
            const query = (document.querySelector('.d3-search')?.value || '').trim().toLowerCase();
            const tourNodeId = (graph.tour || [])[tourIndex]?.nodeId;
            const matches = (node) => {{
              if (!query) return true;
              const haystack = [node.title, node.kind, node.summary, ...(node.details || []), ...(node.files || []).map((file) => file.path || file.label || ''), ...(node.comments || []).map((comment) => `${{comment.author || ''}} ${{comment.body || ''}}`)].join(' ').toLowerCase();
              return haystack.includes(query);
            }};
            const visible = new Set((graph.nodes || []).filter(matches).map((node) => node.id));
            window.d3.selectAll('.d3-node')
              .classed('is-dimmed', (node) => !visible.has(node.id))
              .classed('is-selected', (node) => node.id === selectedNodeId)
              .classed('is-tour-node', (node) => node.id === tourNodeId);
            window.d3.selectAll('.d3-edge').classed('is-dimmed', (edge) => !visible.has(edge.source) || !visible.has(edge.target));
          }}

          function fitToView() {{
            if (!svgSelection || !viewportSelection || !zoomBehavior) return;
            const svg = svgSelection.node();
            const bounds = viewportSelection.node().getBBox();
            const fullWidth = svg.clientWidth || 1000;
            const fullHeight = svg.clientHeight || 700;
            const width = Math.max(bounds.width, 1);
            const height = Math.max(bounds.height, 1);
            const scale = Math.min(1.25, 0.86 / Math.max(width / fullWidth, height / fullHeight));
            const translate = [fullWidth / 2 - scale * (bounds.x + width / 2), fullHeight / 2 - scale * (bounds.y + height / 2)];
            svgSelection.transition().duration(300).call(zoomBehavior.transform, window.d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
          }}
          function focusNode(node) {{
            if (!node || !svgSelection || !zoomBehavior) return;
            const svg = svgSelection.node();
            const scale = Math.max(0.85, window.d3.zoomTransform(svg).k || 1);
            const translate = [(svg.clientWidth || 1000) / 2 - node.x * scale, (svg.clientHeight || 700) / 2 - node.y * scale];
            svgSelection.transition().duration(260).call(zoomBehavior.transform, window.d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
          }}
          function resetZoom() {{ if (svgSelection && zoomBehavior) svgSelection.transition().duration(220).call(zoomBehavior.transform, window.d3.zoomIdentity); }}
          function zoomBy(factor) {{ if (svgSelection && zoomBehavior) svgSelection.transition().duration(140).call(zoomBehavior.scaleBy, factor); }}

          function selectTourStep(index, options = {{}}) {{
            const graph = activeGraph();
            const tour = graph.tour || [];
            if (!tour.length) return;
            tourIndex = Math.max(0, Math.min(index, tour.length - 1));
            const nodes = nodeMap(graph);
            const node = nodes.get(tour[tourIndex].nodeId) || (graph.nodes || [])[0];
            selectedNodeId = node?.id || null;
            renderTour(graph);
            renderDetails(node, graph);
            applyFilters(graph);
            if (!options.noFocus) focusNode(node);
          }}
          function nextTourStep() {{ selectTourStep(tourIndex + 1); }}
          function previousTourStep() {{ selectTourStep(tourIndex - 1); }}
          function restartTour() {{ selectTourStep(0); }}

          function renderActiveGraph(options = {{}}) {{
            const graph = activeGraph();
            if (!graph) throw new Error('No active graph');
            const svg = window.d3.select('#pr-walkthrough-canvas');
            if (svg.empty()) throw new Error('Missing #pr-walkthrough-canvas');
            svg.selectAll('*').remove();
            svgSelection = svg;
            const nodesById = nodeMap(graph);
            const defs = svg.append('defs');
            defs.append('marker').attr('id', `d3-arrowhead-${{graph.id}}`).attr('class', 'd3-edge-arrow').attr('viewBox', '0 -6 12 12').attr('refX', 11).attr('refY', 0).attr('markerWidth', 9).attr('markerHeight', 9).attr('orient', 'auto').attr('markerUnits', 'strokeWidth').style('--edge-color', graph.color || '#868584').append('path').attr('d', 'M0,-6L12,0L0,6Z');
            const root = svg.append('g').attr('class', 'd3-zoom-root');
            viewportSelection = root.append('g').attr('class', 'd3-viewport');
            viewportSelection.append('text').attr('class', 'd3-graph-title').attr('x', -420).attr('y', -300).attr('fill', graph.color || '#a43787').text(graph.label || graph.id);
            const edgeLayer = viewportSelection.append('g').attr('class', 'd3-edges');
            const nodeLayer = viewportSelection.append('g').attr('class', 'd3-nodes');
            const edges = edgeLayer.selectAll('.d3-edge').data(graph.edges || []).join('g').attr('class', 'd3-edge').attr('data-edge-id', (edge, index) => edge.id || `${{edge.source}}-${{edge.target}}-${{index}}`).style('--edge-color', graph.color || '#868584');
            edges.append('path').attr('d', (edge) => pathForEdge(edge, nodesById, graph)).attr('marker-end', `url(#d3-arrowhead-${{graph.id}})`);
            edges.append('text').append('textPath').attr('href', function href(_, index) {{ const path = window.d3.select(edges.nodes()[index]).select('path'); const id = `d3-edge-path-${{graph.id}}-${{index}}`; path.attr('id', id); return `#${{id}}`; }}).attr('startOffset', '50%').attr('text-anchor', 'middle').text((edge) => edge.label || '');
            const nodes = nodeLayer.selectAll('.d3-node').data(graph.nodes || []).join('g').attr('class', (node) => `d3-node${{graph.id === 'system-overview' ? ' is-overview-card' : ''}}`).attr('data-node-id', (node) => node.id).attr('tabindex', 0).attr('role', 'button').attr('aria-label', (node) => node.title).attr('transform', (node) => `translate(${{node.x || 0}}, ${{node.y || 0}})`).style('--node-color', graph.color || '#a43787').on('click keydown', (event, node) => {{
              if (event.type === 'keydown' && event.key !== 'Enter' && event.key !== ' ') return;
              selectedNodeId = node.id;
              const tourPosition = (graph.tour || []).findIndex((step) => step.nodeId === node.id);
              if (tourPosition >= 0) tourIndex = tourPosition;
              renderTour(graph);
              renderDetails(node, graph);
              applyFilters(graph);
            }});
            nodes.append('rect').attr('x', (node) => -nodeWidth(node, graph) / 2).attr('y', (node) => -nodeHeight(node, graph) / 2).attr('width', (node) => nodeWidth(node, graph)).attr('height', (node) => nodeHeight(node, graph)).attr('rx', 12);
            nodes.append('text').attr('class', 'd3-node-kind').attr('x', (node) => -nodeWidth(node, graph) / 2 + 20).attr('y', (node) => -nodeHeight(node, graph) / 2 + 27).text((node) => node.kind || 'point');
            nodes.append('text').attr('class', 'd3-node-title').attr('x', (node) => -nodeWidth(node, graph) / 2 + 20).attr('y', (node) => -nodeHeight(node, graph) / 2 + 53).text((node) => node.title || node.id).call(wrapText, (node) => nodeWidth(node, graph) - 40, 2);
            nodes.append('text').attr('class', 'd3-node-summary').attr('x', (node) => -nodeWidth(node, graph) / 2 + 20).attr('y', (node) => -nodeHeight(node, graph) / 2 + 96).text((node) => node.summary || '').call(wrapText, (node) => nodeWidth(node, graph) - 40, (node) => Number(node.summaryLines || (graph.id === 'system-overview' ? 7 : 2)));
            zoomBehavior = window.d3.zoom().scaleExtent([0.18, 3.5]).on('zoom', (event) => root.attr('transform', event.transform));
            svg.call(zoomBehavior);
            document.querySelectorAll('.d3-graph-toggle').forEach((button) => button.setAttribute('aria-pressed', button.dataset.graphId === graph.id ? 'true' : 'false'));
            selectTourStep(Math.min(tourIndex, Math.max((graph.tour || []).length - 1, 0)), {{ noFocus: true }});
            if (!options.skipFit) window.setTimeout(fitToView, 40);
          }}

          function switchGraph(graphId) {{
            activeGraphId = graphId;
            selectedNodeId = null;
            tourIndex = 0;
            const search = document.querySelector('.d3-search');
            if (search) search.value = '';
            renderActiveGraph();
          }}

          function setupControls() {{
            document.querySelector('[data-d3-action="fit"]')?.addEventListener('click', fitToView);
            document.querySelector('[data-d3-action="reset"]')?.addEventListener('click', resetZoom);
            document.querySelector('[data-d3-action="tour-prev"]')?.addEventListener('click', previousTourStep);
            document.querySelector('[data-d3-action="tour-next"]')?.addEventListener('click', nextTourStep);
            document.querySelector('[data-d3-action="tour-restart"]')?.addEventListener('click', restartTour);
            document.querySelectorAll('.d3-graph-toggle').forEach((button) => button.addEventListener('click', () => switchGraph(button.dataset.graphId)));
            document.querySelector('.d3-search')?.addEventListener('input', () => applyFilters(activeGraph()));
            document.addEventListener('keydown', (event) => {{
              if (event.target?.matches?.('input, textarea')) {{ if (event.key === 'Escape') event.target.blur(); else return; }}
              if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'n') nextTourStep();
              else if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'p') previousTourStep();
              else if (event.key === '1') switchGraph('system-overview');
              else if (event.key === '2') switchGraph('data-flow');
              else if (event.key === '3') switchGraph('code-dependency');
              else if (event.key === '4') switchGraph('user-action');
              else if (event.key === '+' || event.key === '=') zoomBy(1.2);
              else if (event.key === '-') zoomBy(0.82);
              else if (event.key === '0') resetZoom();
              else if (event.key.toLowerCase() === 'f') fitToView();
              else if (event.key === '/') {{ event.preventDefault(); document.querySelector('.d3-search')?.focus(); }}
              else if (event.key === 'Escape') {{ selectedNodeId = null; const search = document.querySelector('.d3-search'); if (search) search.value = ''; renderDetails(null, activeGraph()); applyFilters(activeGraph()); }}
            }});
          }}

          function renderD3Canvas() {{
            if (!window.d3) {{ setError('D3 library was not loaded'); return; }}
            currentData = readInlineData();
            const graphIds = new Set((currentData.graphs || []).map((graph) => graph.id));
            const missing = REQUIRED_GRAPH_IDS.filter((id) => !graphIds.has(id));
            if (missing.length) throw new Error(`Missing required graphs: ${{missing.join(', ')}}`);
            activeGraphId = activeGraphId || (currentData.graphs || [])[0]?.id;
            setupControls();
            renderActiveGraph();
            document.body.classList.add('d3-canvas-ready');
            document.body.classList.remove('d3-canvas-error');
          }}

          function loadD3Runtime() {{
            if (attemptedLoad) return;
            attemptedLoad = true;
            if (window.d3) {{ try {{ renderD3Canvas(); }} catch (error) {{ setError(error); }} return; }}
            const script = document.createElement('script');
            script.src = D3_CDN_URL;
            script.async = true;
            script.onload = () => {{ try {{ renderD3Canvas(); }} catch (error) {{ setError(error); }} }};
            script.onerror = () => setError(`Failed to load pinned D3 CDN script: ${{D3_CDN_URL}}`);
            document.head.appendChild(script);
          }}

          window.prWalkthroughD3Render = renderD3Canvas;
          window.prWalkthroughD3SwitchGraph = switchGraph;
          window.prWalkthroughD3NextTourStep = nextTourStep;
          window.prWalkthroughD3PreviousTourStep = previousTourStep;
          window.prWalkthroughD3FitToView = fitToView;
          if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', loadD3Runtime, {{ once: true }});
          else loadD3Runtime();
        }})();
        </script>
        """
    ).strip()


def graph_controls_markup(data: dict) -> str:
    buttons = "\n".join(
        f'<button class="d3-graph-toggle" type="button" data-graph-id="{html.escape(str(graph.get("id", "")))}" aria-pressed="false" style="--graph-color: {html.escape(str(graph.get("color", "#a43787")))}">{html.escape(str(graph.get("label", graph.get("id", "Graph"))))}</button>'
        for graph in data.get("graphs", [])
    )
    return dedent(
        f"""
        <aside class="d3-control-panel" aria-label="Canvas controls">
          <p class="d3-panel-title">View</p>
          <div class="d3-control-stack">{buttons}</div>
          <p class="d3-panel-title">Tour</p>
          <div class="d3-tour-card" aria-live="polite">
            <div class="d3-tour-step-label">Step 0 / 0</div>
            <h2 class="d3-tour-title">View tour</h2>
            <p class="d3-tour-body">Use Next tour step to start.</p>
          </div>
          <div class="d3-control-stack">
            <button class="d3-control-button" type="button" data-d3-action="tour-prev">Previous tour step</button>
            <button class="d3-control-button" type="button" data-d3-action="tour-next">Next tour step</button>
            <button class="d3-control-button" type="button" data-d3-action="tour-restart">Restart tour</button>
          </div>
          <p class="d3-panel-title">Canvas</p>
          <div class="d3-control-stack">
            <button class="d3-control-button" type="button" data-d3-action="fit">Fit to view</button>
            <button class="d3-control-button" type="button" data-d3-action="reset">Reset zoom</button>
          </div>
          <label class="d3-panel-title" for="d3-node-search">Search active graph</label>
          <input id="d3-node-search" class="d3-search" type="search" placeholder="Search nodes, files, comments" />
          <p class="d3-help">Keyboard: n/→ next, p/← previous, 1 overview, 2 data, 3 code, 4 user, + zoom in, - zoom out, 0 reset, f fit, / search, Esc clear.</p>
        </aside>
        """
    ).strip()


def html_template(data: dict) -> str:
    meta = data.get("meta") or {}
    title = str(meta.get("title") or "PR Walkthrough")
    summary = str(meta.get("summary") or "Interactive PR walkthrough graphs.")
    pr_url = str(meta.get("prUrl") or "")
    base = str(meta.get("baseRef") or "")
    head = str(meta.get("headRef") or "")
    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return dedent(
        f"""
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>{html.escape(title)}</title>
          <style>{d3_canvas_css()}</style>
        </head>
        <body>
          <main class="d3-walkthrough-shell">
            <header class="d3-walkthrough-header">
              <div class="d3-kicker">Warp PR walkthrough</div>
              <h1>{html.escape(title)}</h1>
              <div class="d3-meta-row"><span>{html.escape(base)} ← {html.escape(head)}</span>{f'<a href="{html.escape(pr_url)}" target="_blank" rel="noreferrer">Open PR</a>' if pr_url else ''}</div>
              <p class="d3-summary">{html.escape(summary)}</p>
            </header>
            <section class="d3-canvas-layout">
              {graph_controls_markup(data)}
              <section class="d3-canvas-stage">
                <svg id="pr-walkthrough-canvas" role="img" aria-label="Interactive PR walkthrough graph"></svg>
                <div class="d3-canvas-error" role="alert"></div>
              </section>
              <aside id="pr-walkthrough-details" class="d3-detail-panel" aria-label="Selected point details"></aside>
            </section>
            <script>window.PR_WALKTHROUGH_D3_DATA = {data_json};</script>
            <script id="pr-walkthrough-data" type="application/json">{data_json}</script>
            {d3_canvas_runtime_script()}
          </main>
        </body>
        </html>
        """
    ).strip()


def sample_data() -> dict:
    return {
        "meta": {"title": "Sample PR D3 walkthrough", "prUrl": "", "baseRef": "master", "headRef": "feature", "summary": "Replace this sample graph with PR-specific guided graph tours."},
        "graphs": [
            {
                "id": "system-overview", "label": "System overview", "color": "#c0872a", "summary": "Major touched components.",
                "nodes": [
                    {"id": "surface", "title": "User-facing surface", "kind": "overview card", "x": -220, "y": -80, "width": 360, "height": 220, "summaryLines": 7, "summary": "Use a full paragraph here to define the surface, what code owns it, and why a reviewer needs that concept before reading the PR. Keep this scoped to orientation, not implementation deltas.", "details": ["Explain the stable component."], "files": [], "comments": [], "links": []},
                    {"id": "component", "title": "State or action owner", "kind": "overview card", "x": 220, "y": -80, "width": 360, "height": 220, "summaryLines": 7, "summary": "Use another full paragraph for the next essential concept. If a concept is not needed to understand the review surface, leave it out of the system overview.", "details": ["Explain what this component owns."], "files": [], "comments": [], "links": []},
                ],
                "edges": [],
                "tour": [{"nodeId": "surface", "title": "Start with the surface", "body": "The system overview starts with the smallest useful orientation concept."}, {"nodeId": "component", "title": "Name the owner", "body": "Then identify the state or action owner a reviewer needs to know."}],
            },
            {
                "id": "data-flow", "label": "Data flow graph", "color": "#34895c", "summary": "How state moves.",
                "nodes": [
                    {"id": "intent", "title": "Intent", "kind": "input", "x": -260, "y": -80, "summary": "Spec intent enters the system.", "details": ["Start with the PR intent."], "files": [], "comments": [], "links": []},
                    {"id": "state", "title": "State", "kind": "owner", "x": 80, "y": 20, "summary": "State owner carries the change.", "details": ["Explain the data owner."], "files": [], "comments": [], "links": []},
                ],
                "edges": [{"source": "intent", "target": "state", "label": "flows into"}],
                "tour": [{"nodeId": "intent", "title": "Start with intent", "body": "The data-flow graph begins with the product intent."}, {"nodeId": "state", "title": "Follow state", "body": "Then inspect where state is owned."}],
            },
            {
                "id": "code-dependency", "label": "Code dependency graph", "color": "#2e5d9e", "summary": "How code depends.",
                "nodes": [
                    {"id": "entry", "title": "Entry point", "kind": "entry", "x": -220, "y": -60, "summary": "Changed entry point.", "details": ["Start at the high-level code seam."], "files": [], "comments": [], "links": []},
                    {"id": "leaf", "title": "Leaf dependency", "kind": "leaf", "x": 160, "y": 70, "summary": "Lower-level dependency.", "details": ["Inspect the dependency."], "files": [], "comments": [], "links": []},
                ],
                "edges": [{"source": "entry", "target": "leaf", "label": "depends on"}],
                "tour": [{"nodeId": "entry", "title": "Start at entry", "body": "Begin with the high-level code seam."}, {"nodeId": "leaf", "title": "Drill down", "body": "Then move to the leaf dependency."}],
            },
            {
                "id": "user-action", "label": "User action graph", "color": "#754dac", "summary": "How the user moves.",
                "nodes": [
                    {"id": "surface", "title": "Surface", "kind": "user", "x": -240, "y": -70, "summary": "Where the user starts.", "details": ["Explain the user-facing surface."], "files": [], "comments": [], "links": []},
                    {"id": "feedback", "title": "Feedback", "kind": "result", "x": 160, "y": 70, "summary": "What the user sees.", "details": ["Explain the visible result."], "files": [], "comments": [], "links": []},
                ],
                "edges": [{"source": "surface", "target": "feedback", "label": "user sees"}],
                "tour": [{"nodeId": "surface", "title": "Start at surface", "body": "Begin where the user acts."}, {"nodeId": "feedback", "title": "End at feedback", "body": "End with what the user sees."}],
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit reusable D3 PR walkthrough graph tour snippets.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--css", action="store_true", help="Print the default D3 graph CSS.")
    group.add_argument("--runtime", action="store_true", help="Print pinned-CDN D3 runtime and graph renderer.")
    group.add_argument("--template", action="store_true", help="Print a complete HTML template from graph JSON.")
    group.add_argument("--sample-data", action="store_true", help="Print sample graph JSON.")
    parser.add_argument("--data", type=Path, help="Graph JSON file for --template. If omitted, sample data is used.")
    args = parser.parse_args()
    if args.css:
        print(d3_canvas_css())
    elif args.runtime:
        print(d3_canvas_runtime_script())
    elif args.sample_data:
        print(json.dumps(sample_data(), indent=2))
    elif args.template:
        data = json.loads(args.data.read_text()) if args.data else sample_data()
        print(html_template(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

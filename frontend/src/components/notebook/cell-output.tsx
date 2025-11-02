'use client'

import React from 'react'
import { IOutput } from '@jupyterlab/nbformat'
import AnsiToHtml from 'ansi-to-html'

// Create ANSI converter instance
const ansiConverter = new AnsiToHtml({
  fg: '#e5e7eb',
  bg: '#1f2937',
  newline: true,
  escapeXML: true,
})

interface CellOutputProps {
  outputs: IOutput[]
}

export function CellOutput({ outputs }: CellOutputProps) {
  if (outputs.length === 0) {
    return null
  }

  return (
    <div className="cell-outputs space-y-2 mt-2">
      {outputs.map((output, index) => (
        <OutputRenderer key={index} output={output} />
      ))}
    </div>
  )
}

interface OutputRendererProps {
  output: IOutput
}

function OutputRenderer({ output }: OutputRendererProps) {
  const outputType = output.output_type

  switch (outputType) {
    case 'stream':
      return <StreamOutput output={output as any} />

    case 'execute_result':
    case 'display_data':
      return <DisplayDataOutput output={output as any} />

    case 'error':
      return <ErrorOutput output={output as any} />

    default:
      return <div className="text-xs text-gray-500">Unknown output type: {outputType}</div>
  }
}

// Stream output (stdout, stderr)
function StreamOutput({ output }: { output: any }) {
  const text = Array.isArray(output.text) ? output.text.join('') : output.text
  const isStderr = output.name === 'stderr'
  const htmlContent = ansiConverter.toHtml(text)

  return (
    <pre
      className={`output-stream px-3 py-2 rounded text-sm font-mono overflow-x-auto ${
        isStderr
          ? 'bg-red-500/10 text-red-400 border border-red-500/20'
          : 'bg-gray-800/50 text-gray-300 border border-gray-700/50'
      }`}
      dangerouslySetInnerHTML={{ __html: htmlContent }}
    />
  )
}

// Display data (text, html, images, etc.)
function DisplayDataOutput({ output }: { output: any }) {
  const data = output.data

  // Priority order for rendering different MIME types
  const mimeTypes = [
    'image/png',
    'image/jpeg',
    'image/svg+xml',
    'text/html',
    'application/json',
    'text/plain',
  ]

  for (const mimeType of mimeTypes) {
    if (data[mimeType]) {
      switch (mimeType) {
        case 'image/png':
        case 'image/jpeg':
          return <ImageOutput data={data[mimeType]} mimeType={mimeType} />

        case 'image/svg+xml':
          return <SvgOutput data={data[mimeType]} />

        case 'text/html':
          return <HtmlOutput data={data[mimeType]} />

        case 'application/json':
          return <JsonOutput data={data[mimeType]} />

        case 'text/plain':
          return <PlainTextOutput data={data[mimeType]} />
      }
    }
  }

  return <div className="text-xs text-gray-500">No renderable output</div>
}

// Image output (PNG, JPEG)
function ImageOutput({ data, mimeType }: { data: string; mimeType: string }) {
  const src = `data:${mimeType};base64,${data}`

  return (
    <div className="output-image py-2">
      <img
        src={src}
        alt="Output"
        className="max-w-full h-auto rounded border border-gray-700/50"
      />
    </div>
  )
}

// SVG output
function SvgOutput({ data }: { data: string | string[] }) {
  const svgContent = Array.isArray(data) ? data.join('') : data

  return (
    <div
      className="output-svg py-2"
      dangerouslySetInnerHTML={{ __html: svgContent }}
    />
  )
}

// HTML output
function HtmlOutput({ data }: { data: string | string[] }) {
  const htmlContent = Array.isArray(data) ? data.join('') : data

  return (
    <div
      className="output-html px-3 py-2 rounded bg-gray-800/30 border border-gray-700/50 overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: htmlContent }}
    />
  )
}

// JSON output
function JsonOutput({ data }: { data: any }) {
  const jsonString = JSON.stringify(data, null, 2)

  return (
    <pre className="output-json px-3 py-2 rounded bg-gray-800/50 text-gray-300 border border-gray-700/50 text-sm font-mono overflow-x-auto">
      {jsonString}
    </pre>
  )
}

// Plain text output
function PlainTextOutput({ data }: { data: string | string[] }) {
  const text = Array.isArray(data) ? data.join('') : data
  const htmlContent = ansiConverter.toHtml(text)

  return (
    <pre
      className="output-text px-3 py-2 rounded bg-gray-800/30 text-gray-300 border border-gray-700/50 text-sm font-mono overflow-x-auto whitespace-pre-wrap"
      dangerouslySetInnerHTML={{ __html: htmlContent }}
    />
  )
}

// Error output (tracebacks)
function ErrorOutput({ output }: { output: any }) {
  const { ename, evalue, traceback } = output
  const tracebackHtml = traceback
    ? traceback.map((line: string) => ansiConverter.toHtml(line)).join('\n')
    : ''

  return (
    <div className="output-error px-3 py-2 rounded bg-red-500/10 border border-red-500/30">
      <div className="text-red-400 font-semibold mb-1">
        {ename}: {evalue}
      </div>
      {traceback && traceback.length > 0 && (
        <pre
          className="text-xs text-red-300/80 font-mono overflow-x-auto"
          dangerouslySetInnerHTML={{ __html: tracebackHtml }}
        />
      )}
    </div>
  )
}

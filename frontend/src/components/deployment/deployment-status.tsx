'use client'

import { CheckCircle2, Loader2, XCircle, AlertCircle } from 'lucide-react'
import { useDeploymentStore } from '@/lib/stores/deployment-store'
import { cn } from '@/lib/utils'

function formatPhase(phase: string) {
  return phase
    .split('-')
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ')
}

const iconMap = {
  idle: Loader2,
  validating: Loader2,
  'creating-cluster': Loader2,
  'building-images': Loader2,
  'pushing-images': Loader2,
  'deploying-services': Loader2,
  'deploying-jupyter': Loader2,
  'provisioning-alb': Loader2,
  completed: CheckCircle2,
  failed: XCircle,
} as const

export function DeploymentStatus() {
  const deploymentStatus = useDeploymentStore((state) => state.deploymentStatus)

  if (!deploymentStatus) {
    return null
  }

  const Icon = iconMap[deploymentStatus.phase] ?? Loader2
  const formattedPhase = formatPhase(deploymentStatus.phase)
  const progress = Math.min(Math.max(deploymentStatus.progress ?? 0, 0), 100)
  const isRunning = !['completed', 'failed', 'idle'].includes(deploymentStatus.phase)

  return (
    <div className="paper-stack overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Icon
            className={cn(
              'h-5 w-5',
              isRunning && 'animate-spin text-primary',
              deploymentStatus.phase === 'completed' && 'text-green-600',
              deploymentStatus.phase === 'failed' && 'text-destructive'
            )}
          />
          <div>
            <h2 className="text-lg font-semibold">Deployment Status</h2>
            <p className="text-sm text-muted-foreground">{formattedPhase}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold">{progress}%</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="px-6 py-4 border-b border-border">
        <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full transition-all duration-500',
              deploymentStatus.phase === 'completed' && 'bg-green-600',
              deploymentStatus.phase === 'failed' && 'bg-destructive',
              isRunning && 'bg-primary'
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-3 text-sm">{deploymentStatus.message}</p>
      </div>

      {/* Error Message */}
      {deploymentStatus.error && (
        <div className="px-6 py-4 bg-destructive/10 border-b border-destructive/20 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-destructive">Deployment Failed</p>
            <p className="text-sm text-destructive/80 mt-1">{deploymentStatus.error}</p>
          </div>
        </div>
      )}

      {/* Logs */}
      {deploymentStatus.logs.length > 0 && (
        <div className="px-6 py-4">
          <h3 className="text-sm font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
            Deployment Logs
          </h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {deploymentStatus.logs.map((log, index) => (
              <div
                key={index}
                className="flex items-start gap-2 text-sm font-mono bg-muted/30 rounded px-3 py-2"
              >
                <span className="text-muted-foreground">[{index + 1}]</span>
                <span className="flex-1">{log}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

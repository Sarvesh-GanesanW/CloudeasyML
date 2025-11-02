'use client'

import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { ArrowRight, Lock, MapPin, Play, Settings, Sparkles } from 'lucide-react'
import { GPU_INSTANCES, GPU_FAMILIES, calculateMonthlyCost, type GpuFamily } from '@/lib/data/gpu-types'
import { useDeploymentStore } from '@/lib/stores/deployment-store'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const REGION_OPTIONS = [
  { value: 'us-east-1', label: 'US East · N. Virginia' },
  { value: 'us-west-2', label: 'US West · Oregon' },
  { value: 'eu-west-1', label: 'EU · Ireland' },
  { value: 'eu-central-1', label: 'EU · Frankfurt' },
  { value: 'ap-southeast-1', label: 'APAC · Singapore' },
]

export function DeploymentConfig() {
  const { config, setConfig, startDeployment } = useDeploymentStore()
  const [selectedFamily, setSelectedFamily] = useState<GpuFamily>(
    (config.gpuInstance?.family as GpuFamily) ?? 'G5'
  )

  const filteredInstances = useMemo(
    () => GPU_INSTANCES.filter((inst) => inst.family === selectedFamily),
    [selectedFamily]
  )

  const monthlyCost = useMemo(() => {
    if (!config.gpuInstance) return 0
    return calculateMonthlyCost(config.gpuInstance.pricePerHour) * config.nodeCount
  }, [config.gpuInstance, config.nodeCount])

  const handleDeploy = async () => {
    if (!config.gpuInstance) {
      toast.error('Please select a GPU instance type')
      return
    }
    if (!config.awsAccessKeyId || !config.awsSecretAccessKey) {
      toast.error('Please enter AWS credentials')
      return
    }

    toast.promise(startDeployment(), {
      loading: 'Preparing launch pad...',
      success: 'Deployment is underway—watch the live feed!',
      error: 'Mission aborted. Please review your configuration.',
    })
  }

  return (
    <Card className="paper-stack">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-[#2F6BFF]/25 bg-[#E4ECFF] text-[#1E3A8A] shadow-[0_14px_32px_-24px_rgba(47,107,255,0.45)]">
              <Settings className="h-5 w-5" />
            </span>
            <div>
              <CardTitle className="text-xs font-semibold uppercase tracking-[0.28em] text-[#1E1E1E]">
                Deployment blueprint
              </CardTitle>
              <CardDescription className="text-base text-muted-foreground/80">
                Shape notebooks, clusters, and guardrails from one friendly console.
              </CardDescription>
            </div>
          </div>
          <Badge className="hidden md:inline-flex border-[#2F6BFF]/30 bg-[#E4ECFF] text-[#1E3A8A]">
            <Sparkles className="mr-1 h-3.5 w-3.5 text-[#2F6BFF]" />
            Guided
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <section className="grid gap-4 rounded-2xl border border-[#E5D9C7] bg-white p-6">
          <div className="flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.32em] text-[#915B1A]">
            <Lock className="h-4 w-4" />
            Credentials
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="aws-access-key">AWS Access Key ID</Label>
              <Input
                id="aws-access-key"
                placeholder="AKIA..."
                value={config.awsAccessKeyId}
                onChange={(event) => setConfig({ awsAccessKeyId: event.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="aws-secret-key">AWS Secret Access Key</Label>
              <Input
                id="aws-secret-key"
                type="password"
                placeholder="••••••••••••••••••"
                value={config.awsSecretAccessKey}
                onChange={(event) => setConfig({ awsSecretAccessKey: event.target.value })}
              />
            </div>
          </div>
        </section>

        <section className="grid gap-6 rounded-2xl border border-[#E5D9C7] bg-white p-6">
          <div className="grid gap-2">
            <span className="flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.32em] text-[#915B1A]">
              <MapPin className="h-4 w-4" />
              Deployment surface
            </span>
            <p className="text-sm text-muted-foreground/75">Choose the closest region for low-latency access.</p>
          </div>
          <Select
            value={config.region}
            onChange={(event) => setConfig({ region: event.target.value })}
          >
            {REGION_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>

          <div className="grid gap-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-[0.32em] text-[#915B1A]">
                GPU families
              </span>
              <span className="text-xs text-muted-foreground/70">Dial in a family to refine curated instances.</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {GPU_FAMILIES.map((family) => {
                const isActive = family === selectedFamily
                return (
                  <Button
                    key={family}
                    type="button"
                    variant={isActive ? 'secondary' : 'ghost'}
                    size="sm"
                    className={cn(
                      'rounded-full border border-[#E5D9C7] bg-[#FFFAF0] px-5 text-xs uppercase tracking-[0.3em] text-[#74401A] transition-all',
                      isActive &&
                        'border-[#2F6BFF] bg-[#E4ECFF] text-[#1E3A8A] shadow-[0_18px_40px_-28px_rgba(47,107,255,0.45)]'
                    )}
                    onClick={() => {
                      setSelectedFamily(family)
                      if (config.gpuInstance?.family !== family) {
                        setConfig({ gpuInstance: null })
                      }
                    }}
                  >
                    {family}
                  </Button>
                )
              })}
            </div>
          </div>

          <div className="grid gap-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-[0.32em] text-[#915B1A]">Instance gallery</span>
              <span className="text-xs text-muted-foreground/70">Curated per-family with pricing signals.</span>
            </div>
            <div className="grid max-h-72 gap-3 overflow-y-auto pr-1">
              {filteredInstances.map((instance) => {
                const active = config.gpuInstance?.type === instance.type
                const hourly = instance.pricePerHour
                const monthly = calculateMonthlyCost(hourly)
                return (
                  <button
                    key={instance.type}
                    type="button"
                    onClick={() => setConfig({ gpuInstance: instance })}
                    className={cn(
                      'group flex w-full items-center justify-between rounded-2xl border border-[#E5D9C7] bg-white p-4 text-left transition-all duration-300 hover:-translate-y-1 hover:border-[#2F6BFF] hover:shadow-[0_28px_60px_-50px_rgba(47,107,255,0.35)]',
                      active && 'border-[#2F6BFF] bg-[#E4ECFF]'
                    )}
                  >
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center gap-3">
                        <span className="text-base font-semibold text-foreground">{instance.type}</span>
                        <Badge variant={active ? 'default' : 'outline'}>{instance.gpu}</Badge>
                      </div>
                      <div className="grid gap-2 text-xs text-muted-foreground/80 md:grid-cols-2">
                        <span>{instance.gpuCount} × GPU · {instance.gpuMemory}</span>
                        <span>{instance.vCpus} vCPUs · {instance.memory} RAM</span>
                        <span className="col-span-2 text-[#7A4117]">{instance.useCase}</span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2 text-right">
                      <span className="text-lg font-semibold text-[#2F6BFF]">
                        ${hourly.toFixed(3)}
                        <span className="text-xs text-muted-foreground/70">/hr</span>
                      </span>
                      <span className="text-xs text-muted-foreground/60">${monthly.toFixed(0)} per month</span>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        </section>

        <section className="grid gap-4 rounded-2xl border border-[#E5D9C7] bg-white p-6">
          <div className="flex flex-col gap-2">
            <span className="text-xs font-semibold uppercase tracking-[0.32em] text-[#915B1A]">Node topology</span>
            <p className="text-sm text-muted-foreground/70">
              Define how many workers to spin up alongside your control plane.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="node-count">Total nodes</Label>
              <Input
                id="node-count"
                type="number"
                min={1}
                max={10}
                value={config.nodeCount}
                onChange={(event) => setConfig({ nodeCount: Number(event.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label>Auto scaling</Label>
              <div className="flex items-center justify-between rounded-2xl border border-[#E5D9C7] bg-[#FFFAF0] p-3">
                <span className="text-sm text-muted-foreground/80">Elastic worker group</span>
                <Switch
                  checked={config.autoScaling}
                  onCheckedChange={(checked) => setConfig({ autoScaling: checked })}
                />
              </div>
            </div>
          </div>

          {config.autoScaling && (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="min-nodes">Minimum nodes</Label>
                <Input
                  id="min-nodes"
                  type="number"
                  min={1}
                  value={config.minNodes}
                  onChange={(event) => setConfig({ minNodes: Number(event.target.value) })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max-nodes">Maximum nodes</Label>
                <Input
                  id="max-nodes"
                  type="number"
                  min={config.minNodes || 1}
                  value={config.maxNodes}
                  onChange={(event) => setConfig({ maxNodes: Number(event.target.value) })}
                />
              </div>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Spot instances</Label>
              <div className="flex items-center justify-between rounded-2xl border border-[#E5D9C7] bg-[#FFFAF0] p-3">
                <span className="text-sm text-muted-foreground/80">Leverage AWS market pricing</span>
                <Switch
                  checked={config.useSpotInstances}
                  onCheckedChange={(checked) => setConfig({ useSpotInstances: checked })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Observability</Label>
              <div className="flex items-center justify-between rounded-2xl border border-[#E5D9C7] bg-[#FFFAF0] p-3">
                <span className="text-sm text-muted-foreground/80">Stream metrics &amp; logs</span>
                <Switch
                  checked={config.enableMonitoring}
                  onCheckedChange={(checked) => setConfig({ enableMonitoring: checked })}
                />
              </div>
            </div>
          </div>
        </section>

        <section className="relative overflow-hidden rounded-2xl border border-[#E5D9C7] bg-white p-6">
          <div className="pointer-events-none absolute -right-6 top-0 h-32 w-32 rounded-full bg-[#FFD400]/20 blur-2xl" />
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <span className="text-xs uppercase tracking-[0.35em] text-[#915B1A]">Mission budget</span>
              <div className="flex items-end gap-3">
                <span className="text-4xl font-semibold text-[#2F6BFF]">${monthlyCost.toFixed(2)}</span>
                <span className="pb-1 text-sm text-muted-foreground/70">per month</span>
              </div>
              {config.gpuInstance && (
                <p className="text-xs text-muted-foreground/75">
                  {config.nodeCount}× {config.gpuInstance.type} at ${config.gpuInstance.pricePerHour.toFixed(3)} / hour
                </p>
              )}
            </div>
            <Button
              variant="default"
              size="lg"
              disabled={!config.gpuInstance || !config.awsAccessKeyId}
              onClick={handleDeploy}
              className="w-full md:w-auto"
            >
              <Play className="h-4 w-4" />
              Initiate launch
            </Button>
          </div>
          <div className="mt-4 flex flex-wrap gap-4 text-xs text-muted-foreground/80">
            <span className="inline-flex items-center gap-1 rounded-full border border-[#2F6BFF]/20 bg-[#E4ECFF] px-3 py-1">
              <ArrowRight className="h-3 w-3" />
              Spot savings: up to 70%
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-[#FFD400]/30 bg-[#FFF3B0] px-3 py-1">
              <ArrowRight className="h-3 w-3" />
              End-to-end observability if enabled
            </span>
          </div>
        </section>
      </CardContent>
    </Card>
  )
}

'use client'

import { useState } from 'react'
import { useDeploymentStore } from '@/lib/stores/deployment-store'
import { GPU_INSTANCES, GPU_FAMILIES, calculateMonthlyCost, type GpuFamily } from '@/lib/data/gpu-types'
import { Play, Cpu, DollarSign, MapPin, Settings, Lock } from 'lucide-react'
import { toast } from 'sonner'

export function DeploymentConfig() {
  const { config, setConfig, startDeployment } = useDeploymentStore()
  const [selectedFamily, setSelectedFamily] = useState<GpuFamily>('G5')
  const [showAdvanced, setShowAdvanced] = useState(false)

  const filteredInstances = GPU_INSTANCES.filter((inst) => inst.family === selectedFamily)

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
      loading: 'Starting deployment...',
      success: 'Deployment initiated successfully',
      error: 'Failed to start deployment',
    })
  }

  const monthlyCost = config.gpuInstance
    ? calculateMonthlyCost(config.gpuInstance.pricePerHour) * config.nodeCount
    : 0

  return (
    <div className="glass-morphism rounded-xl p-8 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Settings className="w-6 h-6 text-snowflake-500" />
          Deployment Configuration
        </h2>
        <p className="text-muted-foreground mt-2">
          Configure your GPU-accelerated Jupyter environment
        </p>
      </div>

      {/* AWS Credentials */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-snowflake-500">
          <Lock className="w-4 h-4" />
          AWS Credentials
        </div>

        <div className="space-y-3">
          <input
            type="text"
            placeholder="AWS Access Key ID"
            value={config.awsAccessKeyId}
            onChange={(e) => setConfig({ awsAccessKeyId: e.target.value })}
            className="w-full bg-background/50 border border-border rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-snowflake-500 transition-all"
          />
          <input
            type="password"
            placeholder="AWS Secret Access Key"
            value={config.awsSecretAccessKey}
            onChange={(e) => setConfig({ awsSecretAccessKey: e.target.value })}
            className="w-full bg-background/50 border border-border rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-snowflake-500 transition-all"
          />
        </div>
      </div>

      {/* Region Selection */}
      <div className="space-y-3">
        <label className="flex items-center gap-2 text-sm font-semibold text-snowflake-500">
          <MapPin className="w-4 h-4" />
          AWS Region
        </label>
        <select
          value={config.region}
          onChange={(e) => setConfig({ region: e.target.value })}
          className="w-full bg-background/50 border border-border rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-snowflake-500 transition-all"
        >
          <option value="us-east-1">US East (N. Virginia)</option>
          <option value="us-west-2">US West (Oregon)</option>
          <option value="eu-west-1">EU (Ireland)</option>
          <option value="eu-central-1">EU (Frankfurt)</option>
          <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
        </select>
      </div>

      {/* GPU Family Selection */}
      <div className="space-y-3">
        <label className="flex items-center gap-2 text-sm font-semibold text-snowflake-500">
          <Cpu className="w-4 h-4" />
          GPU Family
        </label>
        <div className="grid grid-cols-3 gap-2">
          {GPU_FAMILIES.map((family) => (
            <button
              key={family}
              onClick={() => setSelectedFamily(family)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                selectedFamily === family
                  ? 'bg-snowflake-500 text-white'
                  : 'bg-background/50 border border-border hover:border-snowflake-500'
              }`}
            >
              {family}
            </button>
          ))}
        </div>
      </div>

      {/* GPU Instance Selection */}
      <div className="space-y-3">
        <label className="text-sm font-semibold text-snowflake-500">
          Instance Type
        </label>
        <div className="max-h-64 overflow-y-auto space-y-2 pr-2">
          {filteredInstances.map((instance) => (
            <button
              key={instance.type}
              onClick={() => setConfig({ gpuInstance: instance })}
              className={`w-full text-left p-4 rounded-lg border transition-all ${
                config.gpuInstance?.type === instance.type
                  ? 'border-snowflake-500 bg-snowflake-500/10'
                  : 'border-border bg-background/30 hover:border-snowflake-500/50'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="font-semibold text-base">{instance.type}</div>
                  <div className="text-xs text-muted-foreground">{instance.gpu}</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-snowflake-500">
                    ${instance.pricePerHour.toFixed(3)}/hr
                  </div>
                  <div className="text-xs text-muted-foreground">
                    ${calculateMonthlyCost(instance.pricePerHour).toFixed(0)}/mo
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
                <div>{instance.gpuCount}x GPU ({instance.gpuMemory})</div>
                <div>{instance.vCpus} vCPUs</div>
                <div>{instance.memory} RAM</div>
                <div className="col-span-2 mt-1 text-snowflake-400">{instance.useCase}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Node Count */}
      <div className="space-y-3">
        <label className="text-sm font-semibold text-snowflake-500">
          Number of Nodes
        </label>
        <input
          type="number"
          min="1"
          max="10"
          value={config.nodeCount}
          onChange={(e) => setConfig({ nodeCount: parseInt(e.target.value) })}
          className="w-full bg-background/50 border border-border rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-snowflake-500 transition-all"
        />
      </div>

      {/* Advanced Options Toggle */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="text-sm text-snowflake-500 hover:text-snowflake-400 transition-colors"
      >
        {showAdvanced ? 'Hide' : 'Show'} Advanced Options
      </button>

      {/* Advanced Options */}
      {showAdvanced && (
        <div className="space-y-4 pt-4 border-t border-border">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Auto Scaling</label>
            <input
              type="checkbox"
              checked={config.autoScaling}
              onChange={(e) => setConfig({ autoScaling: e.target.checked })}
              className="w-5 h-5 rounded border-border"
            />
          </div>
          {config.autoScaling && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-muted-foreground">Min Nodes</label>
                <input
                  type="number"
                  min="1"
                  value={config.minNodes}
                  onChange={(e) => setConfig({ minNodes: parseInt(e.target.value) })}
                  className="w-full mt-1 bg-background/50 border border-border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Max Nodes</label>
                <input
                  type="number"
                  min="1"
                  value={config.maxNodes}
                  onChange={(e) => setConfig({ maxNodes: parseInt(e.target.value) })}
                  className="w-full mt-1 bg-background/50 border border-border rounded px-3 py-2"
                />
              </div>
            </div>
          )}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Use Spot Instances</label>
            <input
              type="checkbox"
              checked={config.useSpotInstances}
              onChange={(e) => setConfig({ useSpotInstances: e.target.checked })}
              className="w-5 h-5 rounded border-border"
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Enable Monitoring</label>
            <input
              type="checkbox"
              checked={config.enableMonitoring}
              onChange={(e) => setConfig({ enableMonitoring: e.target.checked })}
              className="w-5 h-5 rounded border-border"
            />
          </div>
        </div>
      )}

      {/* Cost Estimate */}
      {config.gpuInstance && (
        <div className="bg-snowflake-500/10 border border-snowflake-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-5 h-5 text-snowflake-500" />
            <span className="font-semibold">Estimated Cost</span>
          </div>
          <div className="text-2xl font-bold text-snowflake-500">
            ${monthlyCost.toFixed(2)}/month
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {config.nodeCount}x {config.gpuInstance.type} @ $
            {config.gpuInstance.pricePerHour.toFixed(3)}/hr
          </div>
          {config.useSpotInstances && (
            <div className="text-xs text-green-500 mt-2">
              💡 Spot instances can save up to 70%
            </div>
          )}
        </div>
      )}

      {/* Deploy Button */}
      <button
        onClick={handleDeploy}
        disabled={!config.gpuInstance || !config.awsAccessKeyId}
        className="w-full snowflake-gradient text-white font-semibold py-4 px-6 rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <Play className="w-5 h-5" />
        Deploy Infrastructure
      </button>
    </div>
  )
}

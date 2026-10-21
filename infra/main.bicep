// Existing environment must have network access to managed PostgreSQL.
param location string = resourceGroup().location
param prefix string = 'drishti'
param environmentName string
param identityName string
param registryServer string
param backendImage string
param frontendImage string
param keyVaultUri string
param dashboardUrl string
param cronExpression string = '0 * * * *'
@allowed(['small', 'standard'])
param apiSize string = 'small'
@allowed(['small', 'standard'])
param webSize string = 'small'
@allowed(['small', 'standard'])
param workerSize string = 'small'
@minValue(60)
@maxValue(1800)
param monitorTimeoutSeconds int = 600
param enableTelegram bool = false
var resourceSizes = {
  small: {
    cpu: json('0.25')
    memory: '0.5Gi'
  }
  standard: {
    cpu: json('0.5')
    memory: '1Gi'
  }
}
resource environment 'Microsoft.App/managedEnvironments@2025-01-01' existing = {
  name: environmentName
}
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: identityName
}
var identityBlock = {
  type: 'UserAssigned'
  userAssignedIdentities: {
    '${identity.id}': {
    }
  }
}
var databaseSecret = {
  name: 'database-url'
  keyVaultUrl: '${keyVaultUri}secrets/database-url'
  identity: identity.id
}
var telegramSecrets = enableTelegram ? [
  {
    name: 'telegram-token'
    keyVaultUrl: '${keyVaultUri}secrets/telegram-token'
    identity: identity.id
  }
  {
    name: 'telegram-chats'
    keyVaultUrl: '${keyVaultUri}secrets/telegram-chats'
    identity: identity.id
  }
] : []
var secrets = concat([
  databaseSecret
  {
    name: 'admin-password'
    keyVaultUrl: '${keyVaultUri}secrets/admin-password'
    identity: identity.id
  }
  {
    name: 'session-secret'
    keyVaultUrl: '${keyVaultUri}secrets/session-secret'
    identity: identity.id
  }
], telegramSecrets)
var telegramEnvironment = enableTelegram ? [
  {
    name: 'TELEGRAM_BOT_TOKEN'
    secretRef: 'telegram-token'
  }
  {
    name: 'TELEGRAM_CHAT_IDS'
    secretRef: 'telegram-chats'
  }
] : []
var environmentVariables = concat([
  {
    name: 'DATABASE_URL'
    secretRef: 'database-url'
  }
  {
    name: 'ADMIN_PASSWORD'
    secretRef: 'admin-password'
  }
  {
    name: 'SESSION_SECRET'
    secretRef: 'session-secret'
  }
  {
    name: 'COOKIE_SECURE'
    value: 'true'
  }
  {
    name: 'DASHBOARD_URL'
    value: dashboardUrl
  }
], telegramEnvironment)
var workerEnvironment = concat([
  {
    name: 'DATABASE_URL'
    secretRef: 'database-url'
  }
  {
    name: 'DASHBOARD_URL'
    value: dashboardUrl
  }
], telegramEnvironment)
var registries = [
  {
    server: registryServer
    identity: identity.id
  }
]
resource api 'Microsoft.App/containerApps@2025-01-01' = {
  name: '${prefix}-api'
  location: location
  identity: identityBlock
  properties: {
    managedEnvironmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      secrets: secrets
      registries: registries
      ingress: {
        external: false
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'api'
          image: backendImage
          env: environmentVariables
          resources: resourceSizes[apiSize]
          probes: [
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
}
resource web 'Microsoft.App/containerApps@2025-01-01' = {
  name: '${prefix}-web'
  location: location
  identity: identityBlock
  properties: {
    managedEnvironmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      registries: registries
      ingress: {
        external: true
        targetPort: 3000
        transport: 'http'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'web'
          image: frontendImage
          env: [
            {
              name: 'API_INTERNAL_URL'
              value: 'https://${api.properties.configuration.ingress.fqdn}'
            }
          ]
          resources: resourceSizes[webSize]
          probes: [
            {
              type: 'Readiness'
              httpGet: {
                path: '/'
                port: 3000
              }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
}
resource monitor 'Microsoft.App/jobs@2025-01-01' = {
  name: '${prefix}-monitor'
  location: location
  identity: identityBlock
  properties: {
    environmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      triggerType: 'Schedule'
      replicaTimeout: monitorTimeoutSeconds
      replicaRetryLimit: 0
      secrets: concat([databaseSecret], telegramSecrets)
      registries: registries
      scheduleTriggerConfig: {
        cronExpression: cronExpression
        parallelism: 1
        replicaCompletionCount: 1
      }
    }
    template: {
      containers: [
        {
          name:'monitor'
          image:backendImage
          command:[
            'python'
            '-m'
            'backend.monitor'
          ]
          env:workerEnvironment
          resources:resourceSizes[workerSize]
        }
      ]
    }
  }
}
resource migrate 'Microsoft.App/jobs@2025-01-01' = {
  name: '${prefix}-migrate'
  location: location
  identity: identityBlock
  properties: {
    environmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 300
      replicaRetryLimit: 0
      secrets: [databaseSecret]
      registries: registries
      manualTriggerConfig: {
        parallelism: 1
        replicaCompletionCount: 1
      }
    }
    template: {
      containers: [
        {
          name:'migrate'
          image:backendImage
          command:[
            'sh'
            '-c'
            'alembic upgrade head && python -m backend.bootstrap'
          ]
          env: [
            {
              name: 'DATABASE_URL'
              secretRef: 'database-url'
            }
          ]
          resources:resourceSizes[workerSize]
        }
      ]
    }
  }
}
output dashboard string = 'https://${web.properties.configuration.ingress.fqdn}'
output monitoringJob string = monitor.name
output migrationJob string = migrate.name

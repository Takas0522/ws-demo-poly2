// =============================================================================
// 認証認可サービス Container App モジュール
// =============================================================================
//
// このモジュールは認証認可サービス (Auth Service) の Container App を定義します。
// 共有の Container Apps Environment 上にデプロイされます。
// =============================================================================

@description('環境名 (dev, staging, production)')
param environment string

@description('リージョン')
param location string

@description('タグ')
param tags object

// --- 依存リソースからの入力 ---

@description('Container Apps Environment の ID')
param containerAppsEnvironmentId string

@description('Container Registry のログインサーバー')
param containerRegistryLoginServer string

@description('Container Registry 名')
param containerRegistryName string

@description('Application Insights 接続文字列')
param appInsightsConnectionString string

@description('Cosmos DB エンドポイント')
param cosmosDbEndpoint string

@secure()
@description('JWT Secret Key')
param jwtSecretKey string

@secure()
@description('Service Shared Secret')
param serviceSharedSecret string

// --- スケーリング設定 ---

@description('最小レプリカ数')
param minReplicas int = 0

@description('最大レプリカ数')
param maxReplicas int = 3

// --- CPU/メモリ設定 ---

@description('コンテナの CPU コア数')
param containerCpu string = '0.25'

@description('コンテナのメモリ (Gi)')
param containerMemory string = '0.5Gi'

// -----------------------------------------------------------------------------
// 認証認可サービス (Auth Service)
// -----------------------------------------------------------------------------
resource authServiceApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-auth-${environment}'
  location: location
  tags: union(tags, { Service: 'auth-service' })
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8001
        transport: 'http'
        allowInsecure: false
        corsPolicy: {
          allowedOrigins: ['*'] // デプロイ後に Frontend URL に制限
          allowCredentials: true
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
          allowedHeaders: ['*']
        }
      }
      registries: [
        {
          server: containerRegistryLoginServer
          username: containerRegistryName
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'jwt-secret-key'
          value: jwtSecretKey
        }
        {
          name: 'service-shared-secret'
          value: serviceSharedSecret
        }
        {
          name: 'acr-password'
          value: listCredentials(resourceId('Microsoft.ContainerRegistry/registries', containerRegistryName), '2023-07-01').passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'auth-service'
          image: '${containerRegistryLoginServer}/auth-service:latest'
          env: [
            { name: 'SERVICE_NAME', value: 'auth-service' }
            { name: 'PORT', value: '8001' }
            { name: 'ENVIRONMENT', value: environment }
            { name: 'COSMOS_DB_ENDPOINT', value: cosmosDbEndpoint }
            { name: 'COSMOS_DB_DATABASE', value: 'auth_management' }
            { name: 'JWT_SECRET', secretRef: 'jwt-secret-key' }
            { name: 'JWT_ALGORITHM', value: 'HS256' }
            { name: 'JWT_EXPIRATION_HOURS', value: '24' }
            { name: 'SERVICE_SHARED_SECRET', secretRef: 'service-shared-secret' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
          ]
          resources: {
            cpu: json(containerCpu)
            memory: containerMemory
          }
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------
output fqdn string = authServiceApp.properties.configuration.ingress.fqdn
output name string = authServiceApp.name
output principalId string = authServiceApp.identity.principalId

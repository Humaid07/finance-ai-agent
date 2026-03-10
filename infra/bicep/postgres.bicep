// postgres.bicep - Azure Database for PostgreSQL Flexible Server

@description('PostgreSQL server name (must be globally unique)')
param serverName string

@description('Azure region')
param location string

@description('Database administrator login')
param administratorLogin string

@secure()
@description('Database administrator password')
param administratorPassword string

@description('Database name to create')
param databaseName string

@description('Environment tag')
param environmentName string

@description('PostgreSQL SKU name')
param skuName string = 'Standard_B1ms'

@description('PostgreSQL tier')
param skuTier string = 'Burstable'

resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: serverName
  location: location
  tags: {
    environment: environmentName
    project: 'finance-ai-agent'
  }
  sku: {
    name: skuName
    tier: skuTier
  }
  properties: {
    administratorLogin: administratorLogin
    administratorLoginPassword: administratorPassword
    version: '15'
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    authConfig: {
      activeDirectoryAuth: 'Disabled'
      passwordAuth: 'Enabled'
    }
    network: {
      // Allow Azure services to connect
    }
  }
}

// Create the finance database
resource financeDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-03-01-preview' = {
  parent: postgresServer
  name: databaseName
  properties: {
    charset: 'utf8'
    collation: 'en_US.utf8'
  }
}

// Allow access from Azure services (needed for Azure Functions)
resource allowAzureServices 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = {
  parent: postgresServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

output serverId string = postgresServer.id
output fullyQualifiedDomainName string = postgresServer.properties.fullyQualifiedDomainName
output serverName string = postgresServer.name

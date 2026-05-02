# Deploy status probe

## Service detail (with source + state)
```json
{
  "errors": [
    {
      "message": "Cannot query field \"source\" on type \"Service\".",
      "locations": [
        {
          "line": 1,
          "column": 99
        }
      ],
      "extensions": {
        "code": "GRAPHQL_VALIDATION_FAILED"
      },
      "traceId": "7850594425975341941"
    },
    {
      "message": "Cannot query field \"template\" on type \"ServiceSource\".",
      "locations": [
        {
          "line": 1,
          "column": 277
        }
      ],
      "extensions": {
        "code": "GRAPHQL_VALIDATION_FAILED"
      },
      "traceId": "7850594425975341941"
    },
    {
      "message": "Cannot query field \"suspend\" on type \"ServiceInstance\".",
      "locations": [
        {
          "line": 1,
          "column": 306
        }
      ],
      "extensions": {
        "code": "GRAPHQL_VALIDATION_FAILED"
      },
      "traceId": "7850594425975341941"
    }
  ]
}
```

## All deployments query (project-level)
```json
{
  "data": {
    "deployments": {
      "edges": [
        {
          "node": {
            "id": "f1ae9c38-fc75-4f67-b56d-17bab33d3a8f",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:47:38.415Z",
            "staticUrl": "lumora-production-4071.up.railway.app",
            "url": null,
            "meta": {
              "plan": "trial",
              "repo": "aalmir-erp/lumora",
              "branch": "main",
              "logsV2": true,
              "reason": "deploy",
              "runtime": "V2",
              "buildOnly": false,
              "commitHash": "d5293b1ba69879d8d977daf41810d8052b0e62b6",
              "configFile": "/railway.json",
              "commitAuthor": "aalmir-erp",
              "volumeMounts": [
                "/data"
              ],
              "commitMessage": "status probe workflow",
              "rootDirectory": null,
              "serviceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "buildCommand": null,
                  "nixpacksPlan": null,
                  "watchPatterns": [],
                  "dockerfilePath": "Dockerfile",
                  "buildEnvironment": "V3",
                  "nixpacksConfigPath": null
                },
                "deploy": {
                  "region": null,
                  "runtime": "V2",
                  "numReplicas": 1,
                  "cronSchedule": null,
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "limitOverride": null,
                  "overlapSeconds": null,
                  "drainingSeconds": null,
                  "healthcheckPath": "/api/health",
                  "preDeployCommand": null,
                  "sleepApplication": false,
                  "useLegacyStacker": false,
                  "ipv6EgressEnabled": false,
                  "multiRegionConfig": {
                    "us-west2": {
                      "numReplicas": 1
                    }
                  },
                  "requiredMountPath": null,
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "registryCredentials": null,
                  "restartPolicyMaxRetries": 5
                }
              },
              "nixpacksProviders": [],
              "fileServiceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "dockerfilePath": "Dockerfile"
                },
                "deploy": {
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "healthcheckPath": "/api/health",
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "restartPolicyMaxRetries": 5
                }
              },
              "propertyFileMapping": {
                "build.builder": "$.build.builder",
                "deploy.startCommand": "$.deploy.startCommand",
                "build.dockerfilePath": "$.build.dockerfilePath",
                "deploy.healthcheckPath": "$.deploy.healthcheckPath",
                "deploy.restartPolicyType": "$.deploy.restartPolicyType",
                "deploy.healthcheckTimeout": "$.deploy.healthcheckTimeout",
                "deploy.restartPolicyMaxRetries": "$.deploy.restartPolicyMaxRetries"
              }
            }
          }
        },
        {
          "node": {
            "id": "67b52b16-4b3c-451c-9422-18ce2b81ab3b",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:46:58.501Z",
            "staticUrl": "lumora-production-4071.up.railway.app",
            "url": null,
            "meta": {
              "plan": "trial",
              "repo": "aalmir-erp/lumora",
              "branch": "main",
              "logsV2": true,
              "reason": "deploy",
              "runtime": "V2",
              "buildOnly": false,
              "commitHash": "a6761864ce377b8a9b71c3854224ad47a8317eee",
              "configFile": "/railway.json",
              "commitAuthor": "github-actions[bot]",
              "volumeMounts": [
                "/data"
              ],
              "commitMessage": "deploy: https://lumora-production-4071.up.railway.app",
              "rootDirectory": null,
              "serviceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "buildCommand": null,
                  "nixpacksPlan": null,
                  "watchPatterns": [],
                  "dockerfilePath": "Dockerfile",
                  "buildEnvironment": "V3",
                  "nixpacksConfigPath": null
                },
                "deploy": {
                  "region": null,
                  "runtime": "V2",
                  "numReplicas": 1,
                  "cronSchedule": null,
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "limitOverride": null,
                  "overlapSeconds": null,
                  "drainingSeconds": null,
                  "healthcheckPath": "/api/health",
                  "preDeployCommand": null,
                  "sleepApplication": false,
                  "useLegacyStacker": false,
                  "ipv6EgressEnabled": false,
                  "multiRegionConfig": {
                    "us-west2": {
                      "numReplicas": 1
                    }
                  },
                  "requiredMountPath": null,
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "registryCredentials": null,
                  "restartPolicyMaxRetries": 5
                }
              },
              "nixpacksProviders": [],
              "fileServiceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "dockerfilePath": "Dockerfile"
                },
                "deploy": {
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "healthcheckPath": "/api/health",
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "restartPolicyMaxRetries": 5
                }
              },
              "propertyFileMapping": {
                "build.builder": "$.build.builder",
                "deploy.startCommand": "$.deploy.startCommand",
                "build.dockerfilePath": "$.build.dockerfilePath",
                "deploy.healthcheckPath": "$.deploy.healthcheckPath",
                "deploy.restartPolicyType": "$.deploy.restartPolicyType",
                "deploy.healthcheckTimeout": "$.deploy.healthcheckTimeout",
                "deploy.restartPolicyMaxRetries": "$.deploy.restartPolicyMaxRetries"
              }
            }
          }
        },
        {
          "node": {
            "id": "04c0dd3c-4c83-45a2-b13f-26228f21f1e3",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:37:48.605Z",
            "staticUrl": "lumora-production-4071.up.railway.app",
            "url": null,
            "meta": {
              "plan": "trial",
              "repo": "aalmir-erp/lumora",
              "branch": "main",
              "logsV2": true,
              "reason": "deploy",
              "runtime": "V2",
              "buildOnly": false,
              "commitHash": "53e8d7a50ea0e6d1114084e8bd3e2e2bb43e447f",
              "configFile": "/railway.json",
              "commitAuthor": "",
              "volumeMounts": [
                "/data"
              ],
              "commitMessage": "Deploy via GraphQL only — connect, set vars, deploy, domain",
              "rootDirectory": null,
              "skipBuildCache": true,
              "serviceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "buildCommand": null,
                  "nixpacksPlan": null,
                  "watchPatterns": [],
                  "dockerfilePath": "Dockerfile",
                  "buildEnvironment": "V3",
                  "nixpacksConfigPath": null
                },
                "deploy": {
                  "region": null,
                  "runtime": "V2",
                  "numReplicas": 1,
                  "cronSchedule": null,
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "limitOverride": null,
                  "overlapSeconds": null,
                  "drainingSeconds": null,
                  "healthcheckPath": "/api/health",
                  "preDeployCommand": null,
                  "sleepApplication": false,
                  "useLegacyStacker": false,
                  "ipv6EgressEnabled": false,
                  "multiRegionConfig": {
                    "us-west2": {
                      "numReplicas": 1
                    }
                  },
                  "requiredMountPath": null,
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "registryCredentials": null,
                  "restartPolicyMaxRetries": 5
                }
              },
              "nixpacksProviders": [],
              "fileServiceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "dockerfilePath": "Dockerfile"
                },
                "deploy": {
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "healthcheckPath": "/api/health",
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "restartPolicyMaxRetries": 5
                }
              },
              "ignoreWatchPatterns": true,
              "propertyFileMapping": {
                "build.builder": "$.build.builder",
                "deploy.startCommand": "$.deploy.startCommand",
                "build.dockerfilePath": "$.build.dockerfilePath",
                "deploy.healthcheckPath": "$.deploy.healthcheckPath",
                "deploy.restartPolicyType": "$.deploy.restartPolicyType",
                "deploy.healthcheckTimeout": "$.deploy.healthcheckTimeout",
                "deploy.restartPolicyMaxRetries": "$.deploy.restartPolicyMaxRetries"
              }
            }
          }
        },
        {
          "node": {
            "id": "f59d08f1-5756-4874-9e4a-cf5154cd1a51",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:37:46.029Z",
            "staticUrl": "lumora-production-4071.up.railway.app",
            "url": null,
            "meta": {
              "plan": "trial",
              "repo": "aalmir-erp/lumora",
              "branch": "main",
              "logsV2": true,
              "reason": "deploy",
              "patchId": "be8fc804-f8a1-4f41-b630-fc728c5a2438",
              "runtime": "V2",
              "buildOnly": false,
              "commitHash": "53e8d7a50ea0e6d1114084e8bd3e2e2bb43e447f",
              "configFile": "/railway.json",
              "commitAuthor": "",
              "volumeMounts": [],
              "commitMessage": "Deploy via GraphQL only — connect, set vars, deploy, domain",
              "rootDirectory": null,
              "serviceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "buildCommand": null,
                  "nixpacksPlan": null,
                  "watchPatterns": [],
                  "dockerfilePath": "Dockerfile",
                  "buildEnvironment": "V3",
                  "nixpacksConfigPath": null
                },
                "deploy": {
                  "region": null,
                  "runtime": "V2",
                  "numReplicas": 1,
                  "cronSchedule": null,
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "limitOverride": null,
                  "overlapSeconds": null,
                  "drainingSeconds": null,
                  "healthcheckPath": "/api/health",
                  "preDeployCommand": null,
                  "sleepApplication": false,
                  "useLegacyStacker": false,
                  "ipv6EgressEnabled": false,
                  "multiRegionConfig": {
                    "us-west2": {
                      "numReplicas": 1
                    }
                  },
                  "requiredMountPath": null,
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "registryCredentials": null,
                  "restartPolicyMaxRetries": 5
                }
              },
              "nixpacksProviders": [],
              "fileServiceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "dockerfilePath": "Dockerfile"
                },
                "deploy": {
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "healthcheckPath": "/api/health",
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "restartPolicyMaxRetries": 5
                }
              },
              "ignoreWatchPatterns": true,
              "propertyFileMapping": {
                "build.builder": "$.build.builder",
                "deploy.startCommand": "$.deploy.startCommand",
                "build.dockerfilePath": "$.build.dockerfilePath",
                "deploy.healthcheckPath": "$.deploy.healthcheckPath",
                "deploy.restartPolicyType": "$.deploy.restartPolicyType",
                "deploy.healthcheckTimeout": "$.deploy.healthcheckTimeout",
                "deploy.restartPolicyMaxRetries": "$.deploy.restartPolicyMaxRetries"
              }
            }
          }
        },
        {
          "node": {
            "id": "4f11373d-67f1-4f43-a983-ba98e2fc3d8c",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:37:44.004Z",
            "staticUrl": "lumora-production-4071.up.railway.app",
            "url": null,
            "meta": {
              "plan": "trial",
              "repo": "aalmir-erp/lumora",
              "branch": "main",
              "logsV2": true,
              "reason": "deploy",
              "patchId": "8d0a865b-b86c-41f0-9d2b-6202f08d9020",
              "runtime": "V2",
              "buildOnly": false,
              "commitHash": "53e8d7a50ea0e6d1114084e8bd3e2e2bb43e447f",
              "configFile": "/railway.json",
              "commitAuthor": "",
              "volumeMounts": [],
              "commitMessage": "Deploy via GraphQL only — connect, set vars, deploy, domain",
              "rootDirectory": null,
              "serviceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "buildCommand": null,
                  "nixpacksPlan": null,
                  "watchPatterns": [],
                  "dockerfilePath": "Dockerfile",
                  "buildEnvironment": "V3",
                  "nixpacksConfigPath": null
                },
                "deploy": {
                  "region": null,
                  "runtime": "V2",
                  "numReplicas": 1,
                  "cronSchedule": null,
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "limitOverride": null,
                  "overlapSeconds": null,
                  "drainingSeconds": null,
                  "healthcheckPath": "/api/health",
                  "preDeployCommand": null,
                  "sleepApplication": false,
                  "useLegacyStacker": false,
                  "ipv6EgressEnabled": false,
                  "multiRegionConfig": {
                    "us-west2": {
                      "numReplicas": 1
                    }
                  },
                  "requiredMountPath": null,
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "registryCredentials": null,
                  "restartPolicyMaxRetries": 5
                }
              },
              "nixpacksProviders": [],
              "fileServiceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "dockerfilePath": "Dockerfile"
                },
                "deploy": {
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "healthcheckPath": "/api/health",
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "restartPolicyMaxRetries": 5
                }
              },
              "ignoreWatchPatterns": true,
              "propertyFileMapping": {
                "build.builder": "$.build.builder",
                "deploy.startCommand": "$.deploy.startCommand",
                "build.dockerfilePath": "$.build.dockerfilePath",
                "deploy.healthcheckPath": "$.deploy.healthcheckPath",
                "deploy.restartPolicyType": "$.deploy.restartPolicyType",
                "deploy.healthcheckTimeout": "$.deploy.healthcheckTimeout",
                "deploy.restartPolicyMaxRetries": "$.deploy.restartPolicyMaxRetries"
              }
            }
          }
        },
        {
          "node": {
            "id": "4f00c566-7a92-4585-83d4-df51eb3035d2",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:37:41.454Z",
            "staticUrl": "lumora-production-4071.up.railway.app",
            "url": null,
            "meta": {
              "plan": "trial",
              "repo": "aalmir-erp/lumora",
              "branch": "main",
              "logsV2": true,
              "reason": "deploy",
              "patchId": "c23895db-1f22-412f-92ad-b43bf1a87a85",
              "runtime": "V2",
              "buildOnly": false,
              "commitHash": "53e8d7a50ea0e6d1114084e8bd3e2e2bb43e447f",
              "configFile": "/railway.json",
              "commitAuthor": "",
              "volumeMounts": [],
              "commitMessage": "Deploy via GraphQL only — connect, set vars, deploy, domain",
              "rootDirectory": null,
              "serviceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "buildCommand": null,
                  "nixpacksPlan": null,
                  "watchPatterns": [],
                  "dockerfilePath": "Dockerfile",
                  "buildEnvironment": "V3",
                  "nixpacksConfigPath": null
                },
                "deploy": {
                  "region": null,
                  "runtime": "V2",
                  "numReplicas": 1,
                  "cronSchedule": null,
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "limitOverride": null,
                  "overlapSeconds": null,
                  "drainingSeconds": null,
                  "healthcheckPath": "/api/health",
                  "preDeployCommand": null,
                  "sleepApplication": false,
                  "useLegacyStacker": false,
                  "ipv6EgressEnabled": false,
                  "multiRegionConfig": {
                    "us-west2": {
                      "numReplicas": 1
                    }
                  },
                  "requiredMountPath": null,
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "registryCredentials": null,
                  "restartPolicyMaxRetries": 5
                }
              },
              "nixpacksProviders": [],
              "fileServiceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "dockerfilePath": "Dockerfile"
                },
                "deploy": {
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "healthcheckPath": "/api/health",
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "restartPolicyMaxRetries": 5
                }
              },
              "ignoreWatchPatterns": true,
              "propertyFileMapping": {
                "build.builder": "$.build.builder",
                "deploy.startCommand": "$.deploy.startCommand",
                "build.dockerfilePath": "$.build.dockerfilePath",
                "deploy.healthcheckPath": "$.deploy.healthcheckPath",
                "deploy.restartPolicyType": "$.deploy.restartPolicyType",
                "deploy.healthcheckTimeout": "$.deploy.healthcheckTimeout",
                "deploy.restartPolicyMaxRetries": "$.deploy.restartPolicyMaxRetries"
              }
            }
          }
        },
        {
          "node": {
            "id": "59b8e76f-6dc1-4c29-8415-82c4ed9fbb6a",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:37:40.233Z",
            "staticUrl": "lumora-production-4071.up.railway.app",
            "url": null,
            "meta": {
              "plan": "trial",
              "repo": "aalmir-erp/lumora",
              "branch": "main",
              "logsV2": true,
              "reason": "deploy",
              "patchId": "939fc375-32b8-4aaa-99b6-bc2725c2aae0",
              "runtime": "V2",
              "buildOnly": false,
              "commitHash": "53e8d7a50ea0e6d1114084e8bd3e2e2bb43e447f",
              "configFile": "/railway.json",
              "commitAuthor": "",
              "volumeMounts": [],
              "commitMessage": "Deploy via GraphQL only — connect, set vars, deploy, domain",
              "rootDirectory": null,
              "serviceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "buildCommand": null,
                  "nixpacksPlan": null,
                  "watchPatterns": [],
                  "dockerfilePath": "Dockerfile",
                  "buildEnvironment": "V3",
                  "nixpacksConfigPath": null
                },
                "deploy": {
                  "region": null,
                  "runtime": "V2",
                  "numReplicas": 1,
                  "cronSchedule": null,
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "limitOverride": null,
                  "overlapSeconds": null,
                  "drainingSeconds": null,
                  "healthcheckPath": "/api/health",
                  "preDeployCommand": null,
                  "sleepApplication": false,
                  "useLegacyStacker": false,
                  "ipv6EgressEnabled": false,
                  "multiRegionConfig": {
                    "us-west2": {
                      "numReplicas": 1
                    }
                  },
                  "requiredMountPath": null,
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "registryCredentials": null,
                  "restartPolicyMaxRetries": 5
                }
              },
              "nixpacksProviders": [],
              "fileServiceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "dockerfilePath": "Dockerfile"
                },
                "deploy": {
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "healthcheckPath": "/api/health",
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "restartPolicyMaxRetries": 5
                }
              },
              "ignoreWatchPatterns": true,
              "propertyFileMapping": {
                "build.builder": "$.build.builder",
                "deploy.startCommand": "$.deploy.startCommand",
                "build.dockerfilePath": "$.build.dockerfilePath",
                "deploy.healthcheckPath": "$.deploy.healthcheckPath",
                "deploy.restartPolicyType": "$.deploy.restartPolicyType",
                "deploy.healthcheckTimeout": "$.deploy.healthcheckTimeout",
                "deploy.restartPolicyMaxRetries": "$.deploy.restartPolicyMaxRetries"
              }
            }
          }
        },
        {
          "node": {
            "id": "8208ef74-ccde-4db3-b814-9cd8beba5fa5",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:37:38.725Z",
            "staticUrl": "lumora-production-4071.up.railway.app",
            "url": null,
            "meta": {
              "plan": "trial",
              "repo": "aalmir-erp/lumora",
              "branch": "main",
              "logsV2": true,
              "reason": "deploy",
              "patchId": "1fd6ff59-f0e7-4193-83f9-44f8f20eb682",
              "runtime": "V2",
              "buildOnly": false,
              "commitHash": "53e8d7a50ea0e6d1114084e8bd3e2e2bb43e447f",
              "configFile": "/railway.json",
              "commitAuthor": "",
              "volumeMounts": [],
              "commitMessage": "Deploy via GraphQL only — connect, set vars, deploy, domain",
              "rootDirectory": null,
              "serviceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "buildCommand": null,
                  "nixpacksPlan": null,
                  "watchPatterns": [],
                  "dockerfilePath": "Dockerfile",
                  "buildEnvironment": "V3",
                  "nixpacksConfigPath": null
                },
                "deploy": {
                  "region": null,
                  "runtime": "V2",
                  "numReplicas": 1,
                  "cronSchedule": null,
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "limitOverride": null,
                  "overlapSeconds": null,
                  "drainingSeconds": null,
                  "healthcheckPath": "/api/health",
                  "preDeployCommand": null,
                  "sleepApplication": false,
                  "useLegacyStacker": false,
                  "ipv6EgressEnabled": false,
                  "multiRegionConfig": {
                    "us-west2": {
                      "numReplicas": 1
                    }
                  },
                  "requiredMountPath": null,
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "registryCredentials": null,
                  "restartPolicyMaxRetries": 5
                }
              },
              "nixpacksProviders": [],
              "fileServiceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "dockerfilePath": "Dockerfile"
                },
                "deploy": {
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "healthcheckPath": "/api/health",
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "restartPolicyMaxRetries": 5
                }
              },
              "ignoreWatchPatterns": true,
              "propertyFileMapping": {
                "build.builder": "$.build.builder",
                "deploy.startCommand": "$.deploy.startCommand",
                "build.dockerfilePath": "$.build.dockerfilePath",
                "deploy.healthcheckPath": "$.deploy.healthcheckPath",
                "deploy.restartPolicyType": "$.deploy.restartPolicyType",
                "deploy.healthcheckTimeout": "$.deploy.healthcheckTimeout",
                "deploy.restartPolicyMaxRetries": "$.deploy.restartPolicyMaxRetries"
              }
            }
          }
        },
        {
          "node": {
            "id": "726a484e-325c-4507-8a64-f555db728573",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:37:37.306Z",
            "staticUrl": "lumora-production-4071.up.railway.app",
            "url": null,
            "meta": {
              "plan": "trial",
              "repo": "aalmir-erp/lumora",
              "branch": "main",
              "logsV2": true,
              "reason": "deploy",
              "patchId": "3ac694bc-6bd1-44c5-9290-4258019ce8bc",
              "runtime": "V2",
              "buildOnly": false,
              "commitHash": "53e8d7a50ea0e6d1114084e8bd3e2e2bb43e447f",
              "configFile": "/railway.json",
              "commitAuthor": "",
              "volumeMounts": [],
              "commitMessage": "Deploy via GraphQL only — connect, set vars, deploy, domain",
              "rootDirectory": null,
              "serviceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "buildCommand": null,
                  "nixpacksPlan": null,
                  "watchPatterns": [],
                  "dockerfilePath": "Dockerfile",
                  "buildEnvironment": "V3",
                  "nixpacksConfigPath": null
                },
                "deploy": {
                  "region": null,
                  "runtime": "V2",
                  "numReplicas": 1,
                  "cronSchedule": null,
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "limitOverride": null,
                  "overlapSeconds": null,
                  "drainingSeconds": null,
                  "healthcheckPath": "/api/health",
                  "preDeployCommand": null,
                  "sleepApplication": false,
                  "useLegacyStacker": false,
                  "ipv6EgressEnabled": false,
                  "multiRegionConfig": {
                    "us-west2": {
                      "numReplicas": 1
                    }
                  },
                  "requiredMountPath": null,
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "registryCredentials": null,
                  "restartPolicyMaxRetries": 5
                }
              },
              "nixpacksProviders": [],
              "fileServiceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "dockerfilePath": "Dockerfile"
                },
                "deploy": {
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "healthcheckPath": "/api/health",
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "restartPolicyMaxRetries": 5
                }
              },
              "ignoreWatchPatterns": true,
              "propertyFileMapping": {
                "build.builder": "$.build.builder",
                "deploy.startCommand": "$.deploy.startCommand",
                "build.dockerfilePath": "$.build.dockerfilePath",
                "deploy.healthcheckPath": "$.deploy.healthcheckPath",
                "deploy.restartPolicyType": "$.deploy.restartPolicyType",
                "deploy.healthcheckTimeout": "$.deploy.healthcheckTimeout",
                "deploy.restartPolicyMaxRetries": "$.deploy.restartPolicyMaxRetries"
              }
            }
          }
        },
        {
          "node": {
            "id": "6f9278ab-ddee-450f-8f37-52db79055bc3",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:37:35.564Z",
            "staticUrl": "lumora-production-4071.up.railway.app",
            "url": null,
            "meta": {
              "plan": "trial",
              "repo": "aalmir-erp/lumora",
              "branch": "main",
              "logsV2": true,
              "reason": "deploy",
              "runtime": "V2",
              "buildOnly": false,
              "commitHash": "53e8d7a50ea0e6d1114084e8bd3e2e2bb43e447f",
              "configFile": "/railway.json",
              "commitAuthor": "",
              "volumeMounts": [],
              "commitMessage": "Deploy via GraphQL only — connect, set vars, deploy, domain",
              "rootDirectory": null,
              "serviceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "buildCommand": null,
                  "nixpacksPlan": null,
                  "watchPatterns": [],
                  "dockerfilePath": "Dockerfile",
                  "buildEnvironment": "V3",
                  "nixpacksConfigPath": null
                },
                "deploy": {
                  "region": null,
                  "runtime": "V2",
                  "numReplicas": 1,
                  "cronSchedule": null,
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "limitOverride": null,
                  "overlapSeconds": null,
                  "drainingSeconds": null,
                  "healthcheckPath": "/api/health",
                  "preDeployCommand": null,
                  "sleepApplication": false,
                  "useLegacyStacker": false,
                  "ipv6EgressEnabled": false,
                  "multiRegionConfig": {
                    "us-west2": {
                      "numReplicas": 1
                    }
                  },
                  "requiredMountPath": null,
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "registryCredentials": null,
                  "restartPolicyMaxRetries": 5
                }
              },
              "nixpacksProviders": [],
              "fileServiceManifest": {
                "build": {
                  "builder": "DOCKERFILE",
                  "dockerfilePath": "Dockerfile"
                },
                "deploy": {
                  "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
                  "healthcheckPath": "/api/health",
                  "restartPolicyType": "ON_FAILURE",
                  "healthcheckTimeout": 30,
                  "restartPolicyMaxRetries": 5
                }
              },
              "ignoreWatchPatterns": false,
              "propertyFileMapping": {
                "build.builder": "$.build.builder",
                "deploy.startCommand": "$.deploy.startCommand",
                "build.dockerfilePath": "$.build.dockerfilePath",
                "deploy.healthcheckPath": "$.deploy.healthcheckPath",
                "deploy.restartPolicyType": "$.deploy.restartPolicyType",
                "deploy.healthcheckTimeout": "$.deploy.healthcheckTimeout",
                "deploy.restartPolicyMaxRetries": "$.deploy.restartPolicyMaxRetries"
              }
            }
          }
        }
      ]
    }
  }
}
```

## Health check on assigned domain
HTTP/2 404 
cache-control: public, max-age=5
x-railway-cdn-edge: fastly/cache-iad-kiad7000067-IAD
content-type: application/json
server: railway-edge
x-railway-edge: railway/us-east4-eqdc4a
x-railway-fallback: true
x-railway-request-id: dJMwvBnqToW-co2raP71AA
date: Sat, 02 May 2026 22:47:49 GMT
x-cache: MISS
x-cache-hits: 0
x-served-by: cache-iad-kiad7000067-IAD
content-length: 101

{"status":"error","code":404,"message":"Application not found","request_id":"dJMwvBnqToW-co2raP71AA"}
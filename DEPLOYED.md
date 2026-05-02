# Mutation introspection

## Relevant mutations + arg shapes
```json
{
  "name": "deploymentTriggerCreate",
  "args": [
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "DeploymentTriggerCreateInput",
          "kind": "INPUT_OBJECT",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "deploymentTriggerDelete",
  "args": [
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "String",
          "kind": "SCALAR",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "deploymentTriggerUpdate",
  "args": [
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "String",
          "kind": "SCALAR",
          "ofType": null
        }
      }
    },
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "DeploymentTriggerUpdateInput",
          "kind": "INPUT_OBJECT",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "projectTokenCreate",
  "args": [
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "ProjectTokenCreateInput",
          "kind": "INPUT_OBJECT",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "serviceConnect",
  "args": [
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "String",
          "kind": "SCALAR",
          "ofType": null
        }
      }
    },
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "ServiceConnectInput",
          "kind": "INPUT_OBJECT",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "serviceCreate",
  "args": [
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "ServiceCreateInput",
          "kind": "INPUT_OBJECT",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "serviceDomainCreate",
  "args": [
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "ServiceDomainCreateInput",
          "kind": "INPUT_OBJECT",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "serviceDomainDelete",
  "args": [
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "String",
          "kind": "SCALAR",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "serviceDomainUpdate",
  "args": [
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "ServiceDomainUpdateInput",
          "kind": "INPUT_OBJECT",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "serviceInstanceAutoDeployUpdate",
  "args": [
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "ServiceInstanceAutoDeployUpdateInput",
          "kind": "INPUT_OBJECT",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "serviceInstanceDeploy",
  "args": [
    {
      "name": "commitSha",
      "type": {
        "name": "String",
        "kind": "SCALAR",
        "ofType": null
      }
    },
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "String",
          "kind": "SCALAR",
          "ofType": null
        }
      }
    },
    {
      "name": "latestCommit",
      "type": {
        "name": "Boolean",
        "kind": "SCALAR",
        "ofType": null
      }
    },
    {
      "name": "serviceId",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "String",
          "kind": "SCALAR",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "serviceInstanceDeployV2",
  "args": [
    {
      "name": "commitSha",
      "type": {
        "name": "String",
        "kind": "SCALAR",
        "ofType": null
      }
    },
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "String",
          "kind": "SCALAR",
          "ofType": null
        }
      }
    },
    {
      "name": "serviceId",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "String",
          "kind": "SCALAR",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "serviceInstanceLimitsUpdate",
  "args": [
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "ServiceInstanceLimitsUpdateInput",
          "kind": "INPUT_OBJECT",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "serviceInstanceRedeploy",
  "args": [
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "String",
          "kind": "SCALAR",
          "ofType": null
        }
      }
    },
    {
      "name": "serviceId",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "String",
          "kind": "SCALAR",
          "ofType": null
        }
      }
    }
  ]
}
{
  "name": "serviceInstanceUpdate",
  "args": [
    {
      "name": "environmentId",
      "type": {
        "name": "String",
        "kind": "SCALAR",
        "ofType": null
      }
    },
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "ServiceInstanceUpdateInput",
          "kind": "INPUT_OBJECT",
          "ofType": null
        }
      }
    },
    {
      "name": "serviceId",
      "type": {
        "name": null,
        "kind": "NON_NULL",
        "ofType": {
          "name": "String",
          "kind": "SCALAR",
          "ofType": null
        }
      }
    }
  ]
}
```

## Detail: ServiceCreateInput
```json
{
  "data": {
    "__type": {
      "name": "ServiceCreateInput",
      "inputFields": [
        {
          "name": "branch",
          "type": {
            "name": "String",
            "kind": "SCALAR",
            "ofType": null
          }
        },
        {
          "name": "environmentId",
          "type": {
            "name": "String",
            "kind": "SCALAR",
            "ofType": null
          }
        },
        {
          "name": "icon",
          "type": {
            "name": "String",
            "kind": "SCALAR",
            "ofType": null
          }
        },
        {
          "name": "name",
          "type": {
            "name": "String",
            "kind": "SCALAR",
            "ofType": null
          }
        },
        {
          "name": "projectId",
          "type": {
            "name": null,
            "kind": "NON_NULL",
            "ofType": {
              "name": "String",
              "kind": "SCALAR"
            }
          }
        },
        {
          "name": "registryCredentials",
          "type": {
            "name": "RegistryCredentialsInput",
            "kind": "INPUT_OBJECT",
            "ofType": null
          }
        },
        {
          "name": "source",
          "type": {
            "name": "ServiceSourceInput",
            "kind": "INPUT_OBJECT",
            "ofType": null
          }
        },
        {
          "name": "templateId",
          "type": {
            "name": "String",
            "kind": "SCALAR",
            "ofType": null
          }
        },
        {
          "name": "templateServiceId",
          "type": {
            "name": "String",
            "kind": "SCALAR",
            "ofType": null
          }
        },
        {
          "name": "variables",
          "type": {
            "name": "EnvironmentVariables",
            "kind": "SCALAR",
            "ofType": null
          }
        }
      ]
    }
  }
}
```

## Detail: ServiceConnectInput
```json
{
  "data": {
    "__type": {
      "name": "ServiceConnectInput",
      "inputFields": [
        {
          "name": "branch",
          "type": {
            "name": "String",
            "kind": "SCALAR",
            "ofType": null
          }
        },
        {
          "name": "image",
          "type": {
            "name": "String",
            "kind": "SCALAR",
            "ofType": null
          }
        },
        {
          "name": "repo",
          "type": {
            "name": "String",
            "kind": "SCALAR",
            "ofType": null
          }
        }
      ]
    }
  }
}
```

## Detail: ServiceSourceInput
```json
{
  "data": {
    "__type": {
      "name": "ServiceSourceInput",
      "inputFields": [
        {
          "name": "image",
          "type": {
            "name": "String",
            "kind": "SCALAR",
            "ofType": null
          }
        },
        {
          "name": "repo",
          "type": {
            "name": "String",
            "kind": "SCALAR",
            "ofType": null
          }
        }
      ]
    }
  }
}
```

## Detail: ProjectTokenCreateInput
```json
{
  "data": {
    "__type": {
      "name": "ProjectTokenCreateInput",
      "inputFields": [
        {
          "name": "environmentId",
          "type": {
            "name": null,
            "kind": "NON_NULL",
            "ofType": {
              "name": "String",
              "kind": "SCALAR"
            }
          }
        },
        {
          "name": "name",
          "type": {
            "name": null,
            "kind": "NON_NULL",
            "ofType": {
              "name": "String",
              "kind": "SCALAR"
            }
          }
        },
        {
          "name": "projectId",
          "type": {
            "name": null,
            "kind": "NON_NULL",
            "ofType": {
              "name": "String",
              "kind": "SCALAR"
            }
          }
        }
      ]
    }
  }
}
```

# Lumora deploy — diagnostic

## GraphQL probes
```
--- query: workspaces ---
{"errors":[{"message":"Cannot query field \"workspaces\" on type \"Query\". Did you mean \"workspace\"?","locations":[{"line":1,"column":3}],"extensions":{"code":"GRAPHQL_VALIDATION_FAILED"},"traceId":"1467655546781263611"}]}

--- query: teams ---
{"errors":[{"message":"Cannot query field \"teams\" on type \"Query\". Did you mean \"team\"?","locations":[{"line":1,"column":3}],"extensions":{"code":"GRAPHQL_VALIDATION_FAILED"},"traceId":"8681864641494396841"}]}

--- query: projects ---
{"errors":[{"message":"Field \"projects\" of type \"QueryProjectsConnection!\" must have a selection of subfields. Did you mean \"projects { ... }\"?","locations":[{"line":1,"column":3}],"extensions":{"code":"GRAPHQL_VALIDATION_FAILED"},"traceId":"2045046339694431564"}]}

--- query: projectToken { projectId environmentId } ---
{"errors":[{"message":"Project Token not found","locations":[{"line":1,"column":3}],"path":["projectToken"],"extensions":{"code":"INTERNAL_SERVER_ERROR"},"traceId":"3910135306926956952"}],"data":null}

--- query: me { id email } ---
{"errors":[{"message":"Not Authorized","locations":[{"line":1,"column":3}],"path":["me"],"extensions":{"code":"INTERNAL_SERVER_ERROR"},"traceId":"3228611448008834401"}],"data":null}

```

## Schema (project/workspace/team fields)
```json
{
  "name": "adminVolumeInstancesForVolume",
  "args": [
    {
      "name": "volumeId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "canvasViewMergePreview",
  "args": [
    {
      "name": "sourceEnvironmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "targetEnvironmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "complianceAgreements",
  "args": [
    {
      "name": "workspaceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "deployment",
  "args": [
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "deploymentEvents",
  "args": [
    {
      "name": "after",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "before",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "first",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "last",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "deploymentInstanceExecutions",
  "args": [
    {
      "name": "after",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "before",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "first",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "last",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "deploymentLogs",
  "args": [
    {
      "name": "deploymentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "endDate",
      "type": {
        "name": "DateTime",
        "kind": "SCALAR"
      }
    },
    {
      "name": "filter",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "limit",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "startDate",
      "type": {
        "name": "DateTime",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "deploymentSnapshot",
  "args": [
    {
      "name": "deploymentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "deploymentTriggers",
  "args": [
    {
      "name": "after",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "before",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "first",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "last",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "projectId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "serviceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "deployments",
  "args": [
    {
      "name": "after",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "before",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "first",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "input",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "last",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "environment",
  "args": [
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "projectId",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "environmentLogs",
  "args": [
    {
      "name": "afterDate",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "afterLimit",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "anchorDate",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "beforeDate",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "beforeLimit",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "filter",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "environmentPatch",
  "args": [
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "environmentPatches",
  "args": [
    {
      "name": "after",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "before",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "first",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "last",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "environmentStagedChanges",
  "args": [
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "environments",
  "args": [
    {
      "name": "after",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "before",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "first",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "isEphemeral",
      "type": {
        "name": "Boolean",
        "kind": "SCALAR"
      }
    },
    {
      "name": "last",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "projectId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "externalWorkspaces",
  "args": [
    {
      "name": "projectId",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "functionRuntime",
  "args": [
    {
      "name": "name",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "functionRuntimes",
  "args": []
}
{
  "name": "githubIsRepoNameAvailable",
  "args": [
    {
      "name": "fullRepoName",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "httpDurationMetrics",
  "args": [
    {
      "name": "endDate",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "method",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "path",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "serviceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "startDate",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "statusCode",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "stepSeconds",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "httpMetrics",
  "args": [
    {
      "name": "endDate",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "method",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "path",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "serviceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "startDate",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "statusCode",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "stepSeconds",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "httpMetricsGroupedByStatus",
  "args": [
    {
      "name": "endDate",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "method",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "path",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "serviceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "startDate",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "stepSeconds",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "me",
  "args": []
}
{
  "name": "metrics",
  "args": [
    {
      "name": "averagingWindowSeconds",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "endDate",
      "type": {
        "name": "DateTime",
        "kind": "SCALAR"
      }
    },
    {
      "name": "environmentId",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "groupBy",
      "type": {
        "name": null,
        "kind": "LIST"
      }
    },
    {
      "name": "includeDeleted",
      "type": {
        "name": "Boolean",
        "kind": "SCALAR"
      }
    },
    {
      "name": "measurements",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "projectId",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "sampleRateSeconds",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "serviceId",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "startDate",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "volumeId",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "volumeInstanceExternalId",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "workspaceId",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "privateNetworkEndpointNameAvailable",
  "args": [
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "prefix",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "privateNetworkId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "project",
  "args": [
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "projectCompliance",
  "args": [
    {
      "name": "projectId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "projectInvitation",
  "args": [
    {
      "name": "code",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "projectInvitations",
  "args": [
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "projectInviteCode",
  "args": [
    {
      "name": "projectId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "role",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "projectMembers",
  "args": [
    {
      "name": "projectId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "projectResourceAccess",
  "args": [
    {
      "name": "projectId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "projectToken",
  "args": []
}
{
  "name": "projectTokens",
  "args": [
    {
      "name": "after",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "before",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "first",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "last",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "projectId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "projectWorkspaceMembers",
  "args": [
    {
      "name": "projectId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "projects",
  "args": [
    {
      "name": "after",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "before",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "first",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "includeDeleted",
      "type": {
        "name": "Boolean",
        "kind": "SCALAR"
      }
    },
    {
      "name": "last",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "orderBy",
      "type": {
        "name": "ProjectsOrderBy",
        "kind": "ENUM"
      }
    },
    {
      "name": "userId",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "workspaceId",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    }
  ]
}
{
  "name": "projectsByIds",
  "args": [
    {
      "name": "ids",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "templateMetrics",
  "args": [
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "templateSourceForProject",
  "args": [
    {
      "name": "projectId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "variablesForServiceDeployment",
  "args": [
    {
      "name": "environmentId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "projectId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    },
    {
      "name": "serviceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "volumeInstance",
  "args": [
    {
      "name": "id",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "volumeInstanceBackupList",
  "args": [
    {
      "name": "volumeInstanceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "volumeInstanceBackupScheduleList",
  "args": [
    {
      "name": "volumeInstanceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "workspace",
  "args": [
    {
      "name": "workspaceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "workspaceByCode",
  "args": [
    {
      "name": "code",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "workspaceIdentityProviders",
  "args": [
    {
      "name": "after",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "before",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "first",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "last",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "workspaceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "workspacePolicy",
  "args": [
    {
      "name": "workspaceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
{
  "name": "workspaceTemplates",
  "args": [
    {
      "name": "after",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "before",
      "type": {
        "name": "String",
        "kind": "SCALAR"
      }
    },
    {
      "name": "first",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "last",
      "type": {
        "name": "Int",
        "kind": "SCALAR"
      }
    },
    {
      "name": "workspaceId",
      "type": {
        "name": null,
        "kind": "NON_NULL"
      }
    }
  ]
}
```

## Files railway left in working dir
```
```

## .railway/config.json (if present)
```json
cat: .railway/config.json: No such file or directory
```

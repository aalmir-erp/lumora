# Failed deploy logs

```
deployments:
{
  "data": {
    "deployments": {
      "edges": [
        {
          "node": {
            "id": "d3f02b48-5d64-412a-b6e8-0cbef5e43949",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:48:28.163Z"
          }
        },
        {
          "node": {
            "id": "119dda59-91ee-435d-ac1c-ac1a7faa73c0",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:47:51.805Z"
          }
        },
        {
          "node": {
            "id": "f1ae9c38-fc75-4f67-b56d-17bab33d3a8f",
            "status": "FAILED",
            "createdAt": "2026-05-02T22:47:38.415Z"
          }
        }
      ]
    }
  }
}

=== build logs for d3f02b48-5d64-412a-b6e8-0cbef5e43949 ===
[2026-05-02T22:48:30.825481288Z] info: scheduling build on Metal builder "builder-zoruvv"
[2026-05-02T22:48:33.074414330Z] info: [snapshot] received sha256:732f8919eb475ac9b6f30b98f0e1e2218ce422df618e294084c43d155bb4aa42 md5:81e2c1165bb7840105b0aba9327accda
[2026-05-02T22:48:33.074523584Z] info: receiving snapshot
[2026-05-02T22:48:33.078916315Z] debug: found 'Dockerfile' at 'Dockerfile'
[2026-05-02T22:48:33.078920711Z] debug: found 'railway.json' at 'railway.json'

=== deploy logs for d3f02b48-5d64-412a-b6e8-0cbef5e43949 ===

=== build logs for 119dda59-91ee-435d-ac1c-ac1a7faa73c0 ===
[2026-05-02T22:47:54.192061088Z] info: scheduling build on Metal builder "builder-zoruvv"
[2026-05-02T22:47:56.473683263Z] info: [snapshot] received sha256:3e64b5564fa9ee6c82bcf8c928920554b8b35810437d208005d7db05edd0aaef md5:1b52499c7179660acb46cda9209d51d4
[2026-05-02T22:47:56.473749733Z] info: receiving snapshot
[2026-05-02T22:47:56.479750477Z] debug: found 'Dockerfile' at 'Dockerfile'
[2026-05-02T22:47:56.479757547Z] debug: found 'railway.json' at 'railway.json'
[2026-05-02T22:47:56.479763516Z] debug: skipping 'Dockerfile' at 'whatsapp_bridge/Dockerfile' as it is not rooted at a valid path (root_dir=, fileOpts={acceptChildOfRepoRoot:false})
[2026-05-02T22:47:56.479916335Z] info: analyzing snapshot
[2026-05-02T22:47:56.805164035Z] info: uploading snapshot
[2026-05-02T22:47:56.820724101Z] info: unpacking archive
[2026-05-02T22:47:57.121937820Z] error: dockerfile invalid: docker VOLUME at Line 21 is not supported, use Railway Volumes

=== deploy logs for 119dda59-91ee-435d-ac1c-ac1a7faa73c0 ===

=== build logs for f1ae9c38-fc75-4f67-b56d-17bab33d3a8f ===
[2026-05-02T22:47:42.047201441Z] info: scheduling build on Metal builder "builder-zoruvv"
[2026-05-02T22:47:44.170722922Z] info: [snapshot] received sha256:1bd3f95bd273a53eb202bb8c00d6d0d0dc891998d4155c30edf74bf7b268a46e md5:7fa7b206ca62ba6a08f48ca5c5196107
[2026-05-02T22:47:44.170757344Z] info: receiving snapshot
[2026-05-02T22:47:44.174753250Z] debug: found 'Dockerfile' at 'Dockerfile'
[2026-05-02T22:47:44.174756434Z] debug: found 'railway.json' at 'railway.json'
[2026-05-02T22:47:44.174760180Z] debug: skipping 'Dockerfile' at 'whatsapp_bridge/Dockerfile' as it is not rooted at a valid path (root_dir=, fileOpts={acceptChildOfRepoRoot:false})
[2026-05-02T22:47:44.174806870Z] info: analyzing snapshot
[2026-05-02T22:47:44.504643234Z] info: uploading snapshot
[2026-05-02T22:47:44.508947222Z] info: unpacking archive
[2026-05-02T22:47:44.841920052Z] error: dockerfile invalid: docker VOLUME at Line 21 is not supported, use Railway Volumes

=== deploy logs for f1ae9c38-fc75-4f67-b56d-17bab33d3a8f ===
```

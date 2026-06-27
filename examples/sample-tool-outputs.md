# Sample Tool Outputs

## Tool: `search_nodes`
**Input:**
```json
{
  "query": "Auth"
}
```

**Output:**
```json
{
  "results": [
    {
      "id": "AuthService",
      "type": "Class",
      "metadata": {
        "language": "TypeScript",
        "file": "src/auth/service.ts"
      }
    },
    {
      "id": "AuthController",
      "type": "Class",
      "metadata": {
        "language": "TypeScript",
        "file": "src/auth/controller.ts"
      }
    }
  ]
}
```

## Tool: `read_graph`
**Input:**
```json
{
  "nodeIds": ["AuthService"],
  "depth": 1
}
```

**Output:**
```json
{
  "nodes": [
    {
      "id": "AuthService",
      "type": "Class",
      "metadata": {
        "language": "TypeScript",
        "file": "src/auth/service.ts"
      }
    },
    {
      "id": "UserRepository",
      "type": "Interface",
      "metadata": {
        "language": "TypeScript",
        "file": "src/user/repository.ts"
      }
    }
  ],
  "edges": [
    {
      "source": "AuthService",
      "target": "UserRepository",
      "relation": "depends_on"
    }
  ]
}
```

# Refinement: Client Portal (client-portal)

## Edge Cases
| Edge Case | Handling |
|-----------|----------|
| User accesses other's project | 403 via record rules |
| Share token expired/invalid | 404 page |
| No snapshots yet | Show "Ожидайте первые фото" message |
| Large photo gallery (1000+) | Lazy loading, 20 per page |

# Proposals and Ideas

This folder contains proposal documents for potential future enhancements.

## Files

### .github_issue_csv_schema.md
- **Type**: Technical proposal
- **Date**: October 2025
- **Purpose**: Optimization proposal for historical.csv schema
- **Status**: Not implemented
- **Current state**: Application still uses original schema with all fields

## Schema Proposal Summary

The proposal suggests reducing historical.csv from:
```
date,account,ticker,shares,cost_basis,price,current_value,portfolio_value,allocation_pct
```

To minimal schema:
```
date,account,ticker,shares,price
```

**Benefits**: Smaller file size (~50% reduction), simpler data model

**Considerations**: Need to assess impact on performance calculations and
historical share quantity tracking

**Next steps**: Requires further evaluation and discussion

## Related Documentation

For current data model, see:
- [DEVELOPMENT.md](../../DEVELOPMENT.md) - Technical architecture
- [README.md](../../README.md) - Configuration examples

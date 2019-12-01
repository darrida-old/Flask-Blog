## Post versioning options
- same table 1, additional column for url AND post number
  - Add new post number column (because if each version has a different record with a different unique id, then the id can't be used for post urls - they'd change each time)
  - Migrate from using "id" for urls to the new post number (common between the versions)
  - Decide between using the MAX id number for current post, or a different column
- same table 2, addtional column for common number, but the first id is always updated as the published version
- different table, specific for versioning, with changes moved to main table when they are published
  - this is probably too complicated
## Purpose
Defines how the scraping pipeline selects and processes articles across configured sites during a single run.

## Requirements

### Requirement: Single Article Per Run
When `run_pipeline` is invoked with `do_scrape=True`, the system SHALL process and save at most one new article during that invocation, regardless of how many new articles exist across all configured sites.

#### Scenario: Multiple sites have new articles
- **WHEN** more than one configured site has at least one article not yet present in the store
- **THEN** exactly one article is fetched, parsed, sanitized, fixed, and saved; no other new article is processed in the same run

#### Scenario: No sites have new articles
- **WHEN** every configured site's listing contains only articles already present in the store
- **THEN** no article is processed or saved, and the run completes without raising an error

### Requirement: Random Site Selection
The system SHALL select which site to scrape from by shuffling the configured site list into a random order, then evaluating sites in that shuffled order until one yields an unprocessed article.

#### Scenario: Site with no new articles is skipped
- **WHEN** the first site in the shuffled order has a listing where every article already exists in the store
- **THEN** the system proceeds to fetch the listing of the next site in the shuffled order

#### Scenario: All sites exhausted
- **WHEN** every site in the shuffled order has been checked and none has an unprocessed article
- **THEN** the selection step returns no result and no further sites are checked again in the same run

### Requirement: Random Article Selection Within a Site
When evaluating a site's listing, the system SHALL shuffle the parsed article metas into a random order before checking each one against the store, so the first unprocessed article found is not biased toward listing order.

#### Scenario: First article in listing order already exists
- **WHEN** a site's listing contains both an already-stored article and a new article, and the shuffle places the already-stored one earlier
- **THEN** the system still finds and selects the new article from later in the shuffled order within that same site, without moving on to another site

### Requirement: Injectable Randomness for Selection
The site and article selection logic SHALL accept an optional random number generator parameter; when not supplied, it SHALL default to using the standard library `random` module's shuffling behavior.

#### Scenario: Deterministic selection in tests
- **WHEN** a caller supplies a seeded `random.Random` instance to the selection function
- **THEN** the resulting site and article order is deterministic and reproducible across repeated calls with the same seed

### Requirement: Selection Does Not Mutate Caller-Owned Lists
The shuffle used during site and article selection SHALL operate on a copy of the input lists, not the original lists passed in by the caller.

#### Scenario: Caller's site list is reused after a pipeline run
- **WHEN** `run_pipeline` is called with a list of sites and a list of article metas is parsed from a listing
- **THEN** the original site list and parsed meta list retain their original order after the selection step completes

### Requirement: Listing Fetch Failure Isolation
When selecting a site to scrape, the system SHALL isolate failures from an individual site's listing fetch or article-meta parsing so that one failing site does not abort the selection process for the entire run.

#### Scenario: A site's listing fetch raises an exception
- **WHEN** fetching a site's listing page raises an exception during site selection
- **THEN** the system logs a single warning line identifying the site and the error, waits 1 second, and proceeds to evaluate the next site in the shuffled order without raising

#### Scenario: A site's article-meta parsing raises an exception
- **WHEN** a site's listing page is fetched successfully but parsing its article metas raises an exception
- **THEN** the system logs a single warning line identifying the site and the error, waits 1 second, and proceeds to evaluate the next site in the shuffled order without raising

#### Scenario: A later site succeeds after an earlier site fails
- **WHEN** the first site evaluated in the shuffled order fails its listing fetch and a later site in the order has an unprocessed article
- **THEN** the system selects the unprocessed article from the later site and returns it normally

#### Scenario: Every site fails
- **WHEN** every site in the shuffled order fails its listing fetch or meta parsing
- **THEN** the selection step returns no result, the same as when every site has no new articles

### Requirement: Clean Failure Logging
A listing fetch or parsing failure during site selection SHALL be logged as a single line containing the site name and the error message, without a full stack trace.

#### Scenario: Log output omits traceback
- **WHEN** a site's listing fetch or meta parsing raises an exception
- **THEN** the emitted log record is a warning-level message naming the site and the exception, and does not include the exception's traceback

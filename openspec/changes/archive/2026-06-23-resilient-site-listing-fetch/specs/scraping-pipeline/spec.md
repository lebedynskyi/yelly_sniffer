## ADDED Requirements

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

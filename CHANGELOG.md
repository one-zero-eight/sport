# Changelog

## [MVP v1] - 2025-06-22
### Added
#### Basic frontend created
- Implemented progress page
- Implemented clubs page
- Implemented schedule page
- Implemented FAQ page
- Implemented login page
#### Backend
- Implemented API tests for profile endpoint
- Designed data models: Student, SportSection, Schedule, Registration
- Integrated with existing SSO system (OAuth2/SAML)
- Secured API routes
- Added templates for api v2
## [MVP v2] - 2025-07-06
### Added
#### Frontend
- Fixed bugs
- Visual improvements
- Added confirmation dialog before canceling a training session
- Added "collapse/expand" button for past days in the weekly schedule (collapsed by default)
- Added more training session into the schedule
#### Backend
- Added new tests
### Changed
#### Frontend
- Merged training time and club name dialogs into one
- Made club cards clickable (link to club page) beyond just the "Learn more" button
- Enabled training enrollment directly from the club page
- Improved FAQ search (support multi-word queries, typos, etc.)
- Unified "enroll" and "book activity" terminology
#### Backend
- API refactoring
- Refactored crud structure
- Rewrited urls.py in Rest API style
- Rewrited urls for user actions
- Rewrited path for statistic data
- Rewrited path for user actions files
## MVP [v2.5] - 2025-07-13
### Added
#### Frontend
- Visual improvements
#### Backend
- Added new endpoint for student history
- Turned off old api and turn on new
### Changed
#### Backend
- Added new endpoint for student history
- Made swagger more readable and optimazed endpoints
- Renamed the endpoints
- Updated gitignore
- Fixed the bugs
### Removed
#### Backend
- Removed unused old functions
- Removed window for choosing sport type

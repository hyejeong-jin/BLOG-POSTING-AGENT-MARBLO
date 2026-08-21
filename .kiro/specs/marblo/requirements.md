# Requirements Document

# Marblo (My Blogger) Requirements Document

## Introduction

Marblo is an AI-powered web service designed to help bloggers?”particularly those focused on information delivery content?”reduce content creation time by automating blog post generation. The system specializes in supporting bloggers who create informational content such as real estate listings (loans, jeonse/?„ì„¸, lease options, property details), wedding preparation guides, household information, and similar knowledge-sharing topics. Marblo learns from a blogger's existing writing style, analyzes uploaded photos to extract structured information (location, price, descriptions), and generates information-rich blog posts that match the blogger's voice and tone. The service supports multiple users including the primary blogger and family members, and is built on AWS infrastructure for scalability and reliability.

## Glossary

- **Blogger**: The primary user who creates and manages blog posts; may have an established blog with existing content
- **Family Member**: Secondary users with write permissions to generate content; must be invited by the Blogger
- **Blog Post**: A written article with title, body content, and optional metadata; typically published on external blogging platforms
- **Writing Style Profile**: A learned representation of a specific user's writing patterns including vocabulary, tone, sentence structure, and formatting preferences
- **Photo/Image**: A visual asset uploaded by the user to serve as context for blog post generation
- **Generated Post**: An AI-created blog post generated based on photos and the Writing Style Profile
- **Draft Post**: A generated post that has been saved but not yet published to an external platform
- **Published Post**: A post that has been shared or exported to an external blogging platform
- **Style Learning**: The process of analyzing existing blog posts to extract and build a Writing Style Profile
- **Marblo System**: The complete web application including user management, style learning, post generation, and post management features
- **AWS Infrastructure**: Cloud services used for hosting, storage, and processing (including S3, EC2, Lambda, or equivalent services)
- **Metadata**: Structured information extracted or provided about a photo including description, location, price, date, time, category, and other contextual details
- **Photo Description**: Detailed textual explanation of photo content and context provided by the user
- **Location Information**: Geographic location details (address, coordinates, venue name) associated with a photo, typically the photo location or subject location
- **Price Information**: Cost, market value, or monetary information related to the photo subject (e.g., property price, service cost)
- **Metadata Form**: Structured input interface presenting fields for user to provide photo-related information
- **Metadata Extraction**: Automated process of analyzing photos to detect and suggest metadata values
- **Information-Delivery Content**: Blog posts focused on informing readers about topics such as real estate, wedding preparation, household topics, and educational content
- **Informational Blog Post**: A post that combines photo, structured metadata (location, price, description), and narrative to provide educational or informational value

## Requirements

### Requirement 1: Analyze and Learn User Writing Style

**User Story:** As a blogger, I want to upload my existing blog posts so that the system can learn my writing style and generate new posts that match my voice and tone.

#### Acceptance Criteria

1. WHEN a Blogger uploads existing blog posts, THE Marblo System SHALL parse the content and extract writing characteristics
2. WHEN blog posts are analyzed, THE Writing_Style_Profile SHALL capture vocabulary patterns, sentence structure, tone, and formatting conventions
3. WHERE a Blogger uploads multiple posts over time, THE Marblo System SHALL refine the Writing_Style_Profile with each new upload
4. IF the uploaded content is not valid text, THEN THE Marblo System SHALL return an error message indicating the file format is unsupported
5. THE Marblo System SHALL store the Writing_Style_Profile securely and associate it with the specific Blogger account
6. WHEN a Writing_Style_Profile is updated, THE Marblo System SHALL notify the Blogger that the style has been refreshed

### Requirement 2: Support Photo Upload and Automated Metadata Collection

**User Story:** As a blogger focused on information-delivery content, I want to upload photos and have the system automatically analyze them to extract key information (location, price, descriptions), so that I can quickly provide structured, informational posts.

#### Acceptance Criteria

1. WHEN a Blogger uploads a photo, THE Marblo System SHALL store the photo in AWS S3 and associate it with a unique identifier
2. WHEN a photo is uploaded, THE Marblo System SHALL validate the image format (JPEG, PNG, WebP, GIF) and reject invalid formats
3. IF a photo exceeds the maximum file size of 50MB, THEN THE Marblo System SHALL return an error and request a smaller file
4. THE Marblo System SHALL allow a Blogger to upload multiple photos simultaneously before initiating post generation
5. WHEN a photo is uploaded, THE Marblo System SHALL automatically analyze the photo using computer vision to detect extractable information including location indicators, price text, signage, objects, and scene context
6. WHEN photo analysis completes, THE Marblo System SHALL use OCR (Optical Character Recognition) to extract visible text including prices, addresses, business names, and other readable information
7. WHEN metadata extraction is detected, THE Marblo System SHALL automatically detect and suggest structured metadata fields based on photo content:
   - Location indicators (addresses, landmark names, geographic context) in Location_Information field
   - Price or cost information (numerical values, currency symbols) in Price_Information field
   - Detailed description of photo content in Photo_Description field
   - Relevant category based on content analysis (real estate, wedding, household, etc.) in Category field
8. WHERE metadata extraction confidence is below 80%, THE Marblo System SHALL present fields as suggestions for user verification and confirmation
9. WHEN metadata is extracted, THE Marblo System SHALL present a Metadata_Form to the Blogger with suggested and editable fields for:
   - Photo_Description: AI-generated description of photo content with user edit capability
   - Location_Information: Detected or suggested location details (address, place name, coordinates)
   - Price_Information: Detected or suggested pricing data
   - Date_and_Time: Auto-populated from photo metadata or user-provided
   - Category: Auto-detected category or user-selected
   - Additional_Metadata: User-provided notes, specifications, or contextual details
10. WHERE multiple photos are provided, THE Marblo System SHALL deduplicate similar metadata (e.g., same location across multiple photos) and consolidate for efficiency
11. THE metadata extraction process SHALL complete within 30 seconds per photo and provide clear confidence scores for each extracted field
12. WHERE the Blogger modifies Metadata fields, THE Marblo System SHALL save the changes and associate them with the photo for use in post generation
13. WHEN a Blogger uploads multiple photos, THE Marblo System SHALL collect and organize metadata for all photos in a single session before post generation
14. IF a photo analysis fails or is unclear, THEN THE Marblo System SHALL notify the Blogger and allow manual entry of all Metadata fields
15. WHERE a Blogger needs to remove a photo, THE Marblo System SHALL delete the photo and associated metadata from storage
16. WHEN a Blogger approves extracted metadata, THE Marblo System SHALL save the structured data and use it as a foundation for post generation

### Requirement 3: Generate Information-Rich Blog Post from Photos and Metadata

**User Story:** As a blogger focused on information-delivery content, I want the system to generate blog posts that combine photos with structured metadata (location, price, descriptions) and my writing style, so that I can create informational posts efficiently.

#### Acceptance Criteria

1. WHEN a Blogger provides photos with complete metadata and requests post generation, THE Marblo System SHALL combine photo descriptions, location information, price information, and other metadata with the Writing_Style_Profile
2. WHEN post generation is requested, THE Marblo System SHALL create an Informational_Blog_Post that incorporates:
   - Photo reference and description
   - Location details formatted for reader comprehension
   - Price or cost information presented clearly
   - Supplementary metadata (category, date, specifications)
   - Educational or informational narrative matching the Blogger's writing style
3. WHEN post generation completes, THE Marblo System SHALL generate a blog post including a title, body content (optimized for information delivery), and optional tags or categories
4. THE Generated_Post SHALL follow the Blogger's established tone, vocabulary, and formatting style derived from the Writing_Style_Profile
5. THE Generated_Post body length SHALL be between 800 and 3000 characters by default (extended from standard length for information-rich content), or as specified by the Blogger
6. WHEN the AI model processes the request, THE Marblo System SHALL complete generation within 60 seconds or notify the Blogger of a timeout
7. IF the generated post quality is below acceptable standards, THEN THE Marblo System SHALL inform the Blogger and allow regeneration with different parameters or adjusted metadata
8. WHERE a Blogger provides incomplete metadata, THE Marblo System SHALL generate posts using available information and flag missing fields that could enhance content

### Requirement 4: Allow User Review and Modification of Generated Posts with Metadata Tracking

**User Story:** As a blogger, I want to review the generated post and make edits before it is saved, and I want the metadata used to generate the post to remain connected to the draft, so that I can ensure quality and maintain content traceability.

#### Acceptance Criteria

1. WHEN a post is generated, THE Marblo System SHALL display the generated content in an editable text interface alongside the associated photos and metadata
2. THE Blogger SHALL be able to modify the title, body, tags, metadata fields, and other content of the Generated_Post
3. WHEN the Blogger makes edits, THE Marblo System SHALL save changes to the Draft_Post in real-time
4. THE Marblo System SHALL maintain a connection between the Draft_Post and the source photos and metadata used for generation
5. THE Marblo System SHALL track edit history for each Draft_Post and allow the Blogger to view previous versions along with the metadata changes
6. WHERE the Blogger modifies metadata (location, price, description) in the draft, THE Marblo System SHALL update the associated metadata record
7. WHERE the Blogger rejects the generated post, THE Marblo System SHALL allow regeneration using the same photos, updated metadata, or adjusted parameters
8. WHEN the Blogger completes editing, THE Marblo System SHALL provide an option to save the post as a Draft_Post or directly export it

### Requirement 5: Save and Manage Draft Posts with Photo and Metadata Association

**User Story:** As a blogger, I want to save my edited posts as drafts and manage them over time with their associated photos and metadata, so that I can organize my content workflow and maintain full context for each post.

#### Acceptance Criteria

1. WHEN a Blogger saves a post, THE Marblo System SHALL store it as a Draft_Post with a unique identifier and association to all source photos and metadata
2. THE Marblo System SHALL display a list of all Draft_Posts for the Blogger with creation date, last modified date, title, and associated photo thumbnails
3. THE Blogger SHALL be able to search Draft_Posts by title, date range, location information, price range, or associated photos
4. WHEN a Blogger opens a Draft_Post, THE Marblo System SHALL display the full content, associated photos, original metadata, and edit history
5. WHERE a Blogger deletes a Draft_Post, THE Marblo System SHALL offer an option to preserve the associated photos and metadata for future use or delete them permanently
6. THE Marblo System SHALL automatically save post drafts every 30 seconds to prevent data loss
7. WHEN a Draft_Post is saved, THE Marblo System SHALL store the complete metadata snapshot that was used for generation, enabling later analysis or regeneration with the same parameters

### Requirement 6: Support Multiple Users with Role-Based Access

**User Story:** As a blogger, I want to invite family members to help with post generation and editing, so that I can distribute the workload.

#### Acceptance Criteria

1. WHEN a Blogger invites a Family_Member, THE Marblo System SHALL send an invitation with a unique link or code
2. WHEN a Family_Member accepts the invitation, THE Marblo System SHALL create an account and associate it with the Blogger's account
3. WHERE a Family_Member has write permissions, THE Marblo System SHALL allow post generation and editing under the primary account
4. WHEN a Blogger manages permissions, THE Marblo System SHALL allow the Blogger to grant or revoke Family_Member access
5. THE Marblo System SHALL maintain separate authentication for each user (Blogger and Family_Member)
6. IF a Family_Member attempts to access another Blogger's content, THEN THE Marblo System SHALL deny access and log the attempt

### Requirement 7: Track and Display Generation History with Metadata Details

**User Story:** As a blogger, I want to view a history of all generated posts and their associated photos, metadata, and generation details, so that I can track my content creation progress and understand what information was used.

#### Acceptance Criteria

1. THE Marblo System SHALL maintain a Generation_History log that records each post generation event
2. WHEN the Blogger views the Generation_History, THE record SHALL include generation date, photos used, associated metadata (location, price, description, category), generated title, status (draft/published), and user who generated it
3. THE Marblo System SHALL allow the Blogger to filter Generation_History by date range, user, publication status, location, price range, or category
4. WHERE the Blogger searches the Generation_History, THE Marblo System SHALL return matching records within 2 seconds
5. WHEN a Blogger selects a Generation_History entry, THE Marblo System SHALL display the original photos, complete metadata snapshot, generated post, and all edits made
6. WHERE a Blogger views Generation_History details, THE Marblo System SHALL display metadata that was used for generation including location, price, and description for verification and tracking
7. THE Marblo System SHALL retain Generation_History for a minimum of 12 months

### Requirement 8: Export and Integration with External Blogging Platforms with Metadata Support

**User Story:** As a blogger, I want to export or directly publish my posts to external blogging platforms with associated metadata (location, price, descriptions), so that I can share information-rich content with my audience.

#### Acceptance Criteria

1. WHEN a Blogger completes post editing, THE Marblo System SHALL provide export options for common formats (Markdown, HTML, plain text)
2. WHERE the Blogger selects direct publishing, THE Marblo System SHALL support integration with Naver Blog API or similar platforms
3. WHEN a post is exported or published, THE Marblo System SHALL include structured metadata in an appropriate format (e.g., as formatted text, structured fields, or platform-specific metadata)
   - Location_Information shall be included as a formatted address or venue reference
   - Price_Information shall be included as a formatted price with currency
   - Photo_Description shall be included as alt text or caption
   - Additional metadata (category, date, specifications) shall be included as tags or structured fields where supported by the platform
4. WHEN a post is published to an external platform, THE Marblo System SHALL update the Publication_Status to Published_Post
5. IF the export or publishing process fails, THEN THE Marblo System SHALL provide an error message and allow retry
6. THE Marblo System SHALL allow the Blogger to schedule posts for future publication if the external platform supports it
7. WHEN a post is exported, THE Marblo System SHALL preserve all metadata associations so that the exported format includes source information and structured data

### Requirement 9: Secure Authentication and User Account Management

**User Story:** As a user, I want to securely log in to the Marblo System and manage my account, so that my data is protected.

#### Acceptance Criteria

1. THE Marblo System SHALL require a unique username and strong password (minimum 12 characters, including uppercase, lowercase, numbers, and special characters) for account creation
2. WHEN a user logs in, THE Marblo System SHALL validate credentials against stored hash values and issue a session token
3. WHERE a user forgets their password, THE Marblo System SHALL send a password reset link to their registered email address valid for 24 hours
4. IF login fails after 5 attempts, THEN THE Marblo System SHALL temporarily lock the account and require email verification to unlock
5. THE Marblo System SHALL encrypt all user data at rest using AES-256 encryption
6. WHEN a user logs out, THE Marblo System SHALL invalidate the session token and clear sensitive data from the client

### Requirement 10: Provide Web-Based User Interface

**User Story:** As a blogger, I want to access the Marblo System from any web browser, so that I can use it from any device.

#### Acceptance Criteria

1. THE Marblo System SHALL provide a responsive web interface that functions on desktop browsers (Chrome, Firefox, Safari, Edge) and mobile browsers
2. WHEN a user accesses the web interface, THE page SHALL load completely within 3 seconds
3. THE user interface SHALL display all features including style learning upload, photo upload, post generation, editing, and history management
4. WHERE a user interacts with the interface, THE Marblo System SHALL provide real-time feedback and status updates
5. THE web interface SHALL be deployed on AWS infrastructure (EC2, Lambda, or equivalent)
6. IF the web service becomes unavailable, THEN THE Marblo System SHALL display a maintenance page with expected recovery time

### Requirement 11: Implement AI-Powered Photo Analysis and Metadata Extraction

**User Story:** As a blogger, I want the system to intelligently analyze my photos to extract structured information (location, price, visible text, objects, scenes), so that I can quickly populate metadata and generate information-rich posts.

#### Acceptance Criteria

1. WHEN a photo is provided, THE Marblo System SHALL use computer vision to detect and describe visual elements including objects, scenes, colors, signage, and contextual information
2. WHEN a photo is analyzed, THE Marblo System SHALL use OCR (Optical Character Recognition) to extract visible text including prices, addresses, business names, and other readable information
3. THE Marblo System SHALL automatically detect and suggest metadata fields based on photo content:
   - Location indicators (addresses, landmark names, geographic context) in Location_Information field
   - Price or cost information (numerical values, currency symbols) in Price_Information field
   - Detailed description of photo content in Photo_Description field
   - Relevant category based on content analysis (real estate, wedding, household, etc.) in Category field
4. WHERE metadata extraction confidence is below 80%, THE Marblo System SHALL present fields as suggestions for user verification and confirmation
5. THE photo analysis SHALL generate a textual description (minimum 50 characters, maximum 500 characters) of the image content
6. WHERE multiple photos are provided, THE Marblo System SHALL integrate all photo descriptions and metadata to create a cohesive narrative for post generation
7. IF a photo is unclear or cannot be analyzed, THEN THE Marblo System SHALL inform the Blogger and request clarification, alternative photos, or manual metadata entry
8. WHEN photos are analyzed, THE Marblo System SHALL extract any visible text (OCR) and include it in the context for post generation and metadata population
9. THE photo analysis process SHALL complete within 30 seconds per photo
10. WHEN analysis completes, THE Marblo System SHALL present extracted metadata in an editable Metadata_Form allowing the Blogger to review, confirm, or modify all suggested values before post generation

### Requirement 12: Support Performance and Scalability

**User Story:** As a system operator, I want the Marblo System to scale with increased user demand, so that performance remains consistent.

#### Acceptance Criteria

1. THE Marblo System SHALL support a minimum of 100 concurrent users without degrading response times below 2 seconds
2. WHEN user load increases, THE AWS infrastructure SHALL automatically scale resources to maintain performance
3. THE Marblo System database SHALL handle a minimum of 10,000 blog posts and 50,000 photos across all users
4. WHERE the system experiences high traffic, THE caching layer SHALL reduce database queries by 70%
5. WHEN generating posts, THE Marblo System SHALL queue requests and process them in order to prevent system overload
6. THE system SHALL be monitored for uptime with a minimum availability target of 99.5% monthly

### Requirement 13: Implement Data Backup and Disaster Recovery

**User Story:** As a service operator, I want to protect user data through regular backups and disaster recovery procedures, so that no data is lost.

#### Acceptance Criteria

1. THE Marblo System SHALL perform automated daily backups of all user data, posts, and photos to a redundant storage location
2. WHEN a backup is created, THE Marblo System SHALL verify data integrity through checksum validation
3. IF a data loss incident occurs, THE Marblo System SHALL restore data to the last known good backup within 4 hours
4. THE backup data SHALL be encrypted and stored in a geographically separate AWS region from the primary deployment
5. WHERE a restore operation is needed, THE system operator SHALL have documented recovery procedures and be able to complete recovery within 8 hours
6. THE Marblo System SHALL maintain backup retention for a minimum of 90 days

### Requirement 14: Monitor Logging and Analytics

**User Story:** As a system operator, I want to monitor system performance and user activities, so that I can identify issues and optimize the service.

#### Acceptance Criteria

1. THE Marblo System SHALL log all user activities including login, file uploads, post generation, edits, and exports
2. WHEN logs are created, THE Marblo System SHALL timestamp and categorize each entry (info, warning, error, critical)
3. THE system SHALL store logs in AWS CloudWatch or equivalent service with a minimum retention of 30 days
4. WHERE a critical error occurs, THE Marblo System SHALL automatically alert the system operator through email or SMS
5. WHEN performance metrics are requested, THE Marblo System SHALL provide dashboards showing user activity, post generation times, and system resource usage
6. THE Marblo System SHALL track generation success rates and failures for continuous improvement



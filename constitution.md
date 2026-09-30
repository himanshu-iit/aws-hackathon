# Project Constitution
## Event Entry Guest Tracker System

## Purpose
This constitution establishes the fundamental rules, configurations, and system prompts that govern the development, maintenance, and operation of the Event Entry Guest Tracker project. All team members, systems, and automated agents must adhere to these rules.

## Core Principles
1. **Transparency**: All project decisions and changes must be documented
2. **Accountability**: Clear responsibility assignment for all tasks
3. **Consistency**: Uniform application of rules across the project
4. **Security**: Protection of user data and system integrity
5. **Maintainability**: Systems designed for long-term sustainability

---

## Rule 1: Prompt Tracking System

**Rule Text**:
```
projectprompttracker.md document serves as the official prompt tracker for the Event Entry Guest Tracker project. It automatically records every prompt and corresponding response summary to maintain a complete history of project development decisions and requirements. This needs to be updated by AI agent on each prompt completion.
```

### Detailed Specifications:

#### 1.1 Document Purpose
- Serves as the canonical record of all project prompts and responses
- Maintains historical context for design decisions
- Provides audit trail for project requirements evolution
- Enables transparency in AI-assisted development

#### 1.2 Update Requirements
- **Update Trigger**: After completion of each user prompt
- **Update Agent**: AI development agent responsible for the response
- **Update Timing**: Immediately following prompt response delivery
- **Update Method**: Automatic or manual as specified by available tools

#### 1.3 Content Requirements
Each prompt entry must include:
- **Prompt Number**: Sequential identifier
- **Timestamp**: Date and time of prompt
- **Full Prompt Text**: Exact user input
- **Response Summary**: Concise summary of AI actions and decisions
- **Files Modified**: List of files created or changed
- **Key Decisions**: Important design or implementation choices made

#### 1.4 Format Standards
- Use Markdown formatting for readability
- Maintain chronological order
- Include section headers for organization
- Provide clear separation between entries
- Include project status updates periodically

#### 1.5 Maintenance Rules
- The document must be kept in the project root directory
- No deletions of historical entries allowed
- Corrections must be added as amendments, not replacements
- Regular validation of completeness and accuracy
- Backup included in version control system

#### 1.6 Accessibility
- Read access granted to all project stakeholders
- Write access limited to authorized AI agents and project leads
- Included in project documentation package
- Referenced in project meetings and reviews

#### 1.7 Compliance Verification
- Weekly review of prompt tracking compliance
- Validation that all prompts are recorded
- Verification of response summary accuracy
- Confirmation of timestamp consistency
- Audit of file modification records

#### 1.8 Non-Compliance Handling
- Missing entries must be reconstructed from available logs
- Inaccurate summaries require correction entries
- System alerts for missed updates
- Review of update processes for improvement
- Documentation of any compliance issues

### Implementation Guidelines:

#### For AI Agents:
1. After responding to any user prompt:
   - Open `projectprompttracker.md`
   - Add new prompt entry following the format
   - Update project status summary if needed
   - Increment prompt counter
   - Update last modified timestamp

2. Entry format template:
   ```
   ### Prompt [N]
   **Timestamp**: [YYYY-MM-DD HH:MM:SS]
   **Full Prompt**: 
   ```
   [Exact prompt text]
   ```
   **Response Summary**:
   - [Action 1]
   - [Action 2]
   - [Key decision made]
   - [Files modified: file1, file2]
   
   **Project Impact**: [Brief description of how this affects the project]
   ```

#### For Human Team Members:
1. Review the prompt tracker regularly
2. Verify that your interactions are recorded
3. Report any discrepancies
4. Use the tracker for historical reference
5. Contribute to maintenance when required

#### For Project Management:
1. Include prompt tracker in project reviews
2. Use for requirement traceability
3. Reference in status reports
4. Ensure compliance with this rule
5. Archive with project documentation

### Technical Implementation Notes:

#### Automated Update Methods:
1. **Hook System** (Preferred):
   - Implement PostToolUse hook
   - Trigger on relevant tool executions
   - Automatically append to tracker
   - Include context from tool outputs

2. **Manual Update Process** (Fallback):
   - AI agent manually updates after each prompt
   - Follows standardized format
   - Includes all required information
   - Verified by next prompt

3. **Hybrid Approach**:
   - Automated capture of prompt text
   - Manual summarization of responses
   - Systematic organization of entries
   - Regular quality checks

#### File Location and Structure:
- **Path**: `/projectprompttracker.md` (project root)
- **Format**: Markdown with consistent headers
- **Sections**: Constitution, History, Status, Instructions
- **Backup**: Included in Git repository
- **Access**: Readable by all, writable by AI/system

#### Quality Standards:
- **Completeness**: 100% of prompts recorded
- **Accuracy**: Faithful representation of prompts and responses
- **Timeliness**: Updated within same session
- **Consistency**: Uniform format across all entries
- **Usefulness**: Provides value for project understanding

---

## Rule Status
- **Rule 1**: ACTIVE (Established 2026-09-30)
- **Next Rule**: To be defined as project evolves
- **Amendment Process**: Requires project lead approval

## Document Information
- **Created**: 2026-09-30
- **Version**: 1.0
- **Owner**: Project Lead / AI System
- **Review Schedule**: Monthly
- **Amendment History**: Initial version

---

*This constitution is a living document that will evolve with the project. Additional rules will be added as needed to govern project development, configuration, and system behavior.*
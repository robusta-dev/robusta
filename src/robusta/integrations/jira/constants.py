from robusta.core.model.severity import FindingSeverity

SEVERITY_JIRA_ID = {
    FindingSeverity.HIGH: "Critical",    # Default name mapping
    FindingSeverity.MEDIUM: "Major",
    FindingSeverity.LOW: "Minor",
    FindingSeverity.INFO: "Minor",
}

SEVERITY_JIRA_FALLBACK_ID = {           # Standard Jira IDs as last resort
    FindingSeverity.HIGH: "1",    # Highest
    FindingSeverity.MEDIUM: "2",  # High
    FindingSeverity.LOW: "3",     # Medium
    FindingSeverity.INFO: "4",    # Low
} 

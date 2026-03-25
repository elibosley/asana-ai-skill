# Workflow Patterns Reference

When the AI receives `board --context` output, use these patterns to analyze
the project and recommend Asana rules the user should create in the UI.

## Bottleneck Detection Patterns

### Section Pile-Up
**Signal:** A section contains >40% of all project tasks.
**Diagnosis:** Tasks are accumulating in one stage — likely a bottleneck or
catch-all section with no exit criteria.
**Rule to recommend:**
```
RULE: Auto-move stale tasks from [Section]
TRIGGER: Task is added to [Section]
ACTION: Set due date to 3 days from now
---
RULE: Notify on pile-up in [Section]
TRIGGER: Task due date is approaching
ACTION: Move task to "Needs Review" / assign to lead
```

### Stale Tasks (>30 days without modification)
**Signal:** `staleness.modified_over_30d` is a significant portion of tasks.
**Diagnosis:** Tasks are forgotten or blocked without visibility.
**Rule to recommend:**
```
RULE: Flag stale tasks
TRIGGER: Task is not modified for 14 days (use due date approaching as proxy)
ACTION: Add comment "@assignee — this task hasn't been updated. Still active?"
---
RULE: Auto-set review dates
TRIGGER: Task added to project
ACTION: Set due date to 2 weeks from now (forces periodic review)
```

### Missing Custom Fields (<50% coverage)
**Signal:** A custom field's `coverage_pct` is below 50%.
**Diagnosis:** The field exists but isn't being used consistently — either it's
not useful or people forget to fill it.
**Rule to recommend:**
```
RULE: Auto-set [Field] on new tasks
TRIGGER: Task added to project
ACTION: Set [Field] to default value
---
RULE: Set [Field] on section move
TRIGGER: Task moved to [Section]
ACTION: Set [Field] to [appropriate value for that stage]
```

### Unassigned Tasks (>20% unassigned)
**Signal:** `assignee_distribution.unassigned` / total > 0.2
**Diagnosis:** Tasks are created without ownership — they'll drift.
**Rule to recommend:**
```
RULE: Assign tasks on creation
TRIGGER: Task added to project
ACTION: Assign to project lead / team inbox
---
RULE: Assign on section move
TRIGGER: Task moved to "In Progress"
ACTION: If unassigned, assign to task creator
```

### No Due Dates (>50% without dates)
**Signal:** `date_coverage.coverage_pct` < 50
**Diagnosis:** No time pressure, no prioritization signal.
**Rule to recommend:**
```
RULE: Default due date on creation
TRIGGER: Task added to project
ACTION: Set due date to 1 week from now
---
RULE: Set due date on "In Progress"
TRIGGER: Task moved to "In Progress"
ACTION: Set due date to 3 days from now
```

### Overdue Tasks
**Signal:** `date_coverage.overdue` > 0
**Diagnosis:** Deadlines are being missed — either unrealistic or unmonitored.
**Rule to recommend:**
```
RULE: Escalate overdue tasks
TRIGGER: Task due date is past
ACTION: Move to "Blocked / Needs Attention" section + notify project lead
```

## Common Asana Rule Templates

These are the most useful Asana rules to recommend based on project type:

### Kanban Board
1. **Task moved to "Done"** → Mark task complete
2. **Task marked complete** → Move to "Done" section
3. **Task moved to "In Progress"** → Set due date if empty
4. **Task added to project** → Move to "Backlog" section

### Sprint Board
1. **Task added to project** → Set custom field "Sprint" to current sprint
2. **Task moved to "In Review"** → Add reviewer as follower
3. **Task marked complete** → Set "Points" if empty (prompt for estimate)

### Bug Tracker
1. **Task added to project** → Set priority to "Medium" (default)
2. **Task moved to "Fixed"** → Add QA assignee as follower
3. **Custom field "Severity" changed to "Critical"** → Move to top of "To Do"

## How to Create a Rule in Asana (Step-by-Step)

1. Open the project in Asana
2. Click **Customize** (top-right of project view)
3. Click **Rules** in the sidebar
4. Click **+ Add Rule**
5. Choose a trigger (e.g., "Task moved to a section")
6. Configure the trigger details (e.g., which section)
7. Optionally add a condition (e.g., "If custom field is...")
8. Choose an action (e.g., "Set custom field", "Move to section", "Add comment")
9. Configure the action details
10. Name the rule and click **Create Rule**

### Finding the Trigger Identifier (for `trigger-rule` command)

To use the `trigger-rule` CLI command, you need a rule with an
"Incoming web request" trigger:

1. Open the project → **Customize** → **Rules** → **+ Add Rule**
2. Under triggers, select **Incoming web request**
3. Asana will show a URL like:
   `https://app.asana.com/api/1.0/rule_triggers/IDENTIFIER/run`
4. The `IDENTIFIER` is the trigger identifier you pass to `trigger-rule`
5. Configure the rule's actions (what should happen when triggered)
6. Save the rule

Then trigger it with:
```bash
asana trigger-rule IDENTIFIER --task TASK_GID
```

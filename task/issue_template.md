# Issue #{N}: {Title}

**Status:** 🔵 IN PROGRESS | ✅ COMPLETED | ❌ BLOCKED
**Created:** YYYY-MM-DD
**Completed:** YYYY-MM-DD
**Branch:** `feature/{name}` | `fix/{name}` | `optimize/{name}`

## Overview

{Brief description of what needs to be done}

## Plan

### Phase 1: {Name}
**Goal:** {Objective}
**Estimated time:** X hours

**Steps:**
1. {Step 1}
2. {Step 2}

### Phase 2: {Name}
{Repeat pattern}

## Implementation

### Phase 1: {Name} ✅ COMPLETED

**What was done:**
- {Change 1}
- {Change 2}

**Results:**
- {Metric}: {before} → {after} ({improvement})

**Commits:**
- `{hash}`: {message}

**Learnings - Phase 1:**

**✅ What Worked:**
1. **{Pattern}** - {Why it worked well}

**❌ Mistakes:**
1. **{Mistake}** - {What went wrong}
   - **Fix:** {How it was solved}
   - **Lesson:** {What to do differently next time}

**📚 Patterns to Reuse:**
- {Extractable pattern for future use}

### Phase 2: {Name} {STATUS}

{Repeat pattern for each phase}

## Overall Learnings

**Key Takeaways:**
1. {Lesson 1}
2. {Lesson 2}

**For Future Projects:**
- {Pattern to apply to other projects}

**Documentation Created:**
- Added to `doc/issue_history/issue{N}.md`

## Closing

**Final Status:** {SUCCESS | PARTIAL | FAILED}

**Next Steps:**
- {Follow-up task if any}

---

## How to Use This Template

**When creating an issue:**
```bash
gh issue create --title "Feature/Bug/Optimize: description" --body-file task/issue_template.md
```

**During implementation:**
1. Update with commits and results after each phase
2. Document mistakes immediately (while fresh)
3. Test on preview deployment between phases

**When closing:**
```bash
gh issue comment {N} --body "$(cat doc/issue_history/issue{N}.md)"
gh issue close {N} --comment "merged to main, learnings documented"
gh issue edit {N} --add-label "completed,dev-history"
```

**Why track learnings?**
- Prevents repeating mistakes
- Builds institutional knowledge
- Helps other developers
- Documents pattern evolution

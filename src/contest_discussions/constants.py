"""Fixed IDs and text for the NoviSteps-Writeups repository.

See: https://github.com/AtCoder-NoviSteps/NoviSteps-Writeups
"""

# `gh api graphql -f query='query { repository(owner: "AtCoder-NoviSteps", name: "NoviSteps-Writeups") { id } }'`
REPOSITORY_ID = "R_kgDOTNgHyw"

# "General" discussion category.
# `gh api graphql -f query='query { repository(owner: "AtCoder-NoviSteps", name: "NoviSteps-Writeups") { discussionCategories(first: 10) { nodes { id name } } } }'`
GENERAL_CATEGORY_ID = "DIC_kwDOTNgHy84DAe9x"

DISCUSSION_BODY = "問題の感想や気づきを投稿・共有するスペースです"

# How many recent ABCs to check for missing discussions. Covers up to 3 missed
# weekly cron runs in a row, so a single transient failure self-heals next run.
CONTESTS_TO_CHECK = 3

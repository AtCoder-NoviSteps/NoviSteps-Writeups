"""Fixed IDs and text for the NoviSteps-Writeups repository.

See: https://github.com/AtCoder-NoviSteps/NoviSteps-Writeups
"""

# `gh api graphql -f query='query { repository(owner: "AtCoder-NoviSteps", name: "NoviSteps-Writeups") { id } }'`
REPOSITORY_ID = "R_kgDOTNgHyw"

# "General" discussion category.
# `gh api graphql -f query='query { repository(owner: "AtCoder-NoviSteps", name: "NoviSteps-Writeups") { discussionCategories(first: 10) { nodes { id name } } } }'`
GENERAL_CATEGORY_ID = "DIC_kwDOTNgHy84DAe9x"

DISCUSSION_BODY = "問題の感想や気づきを投稿・共有するスペースです"

# 週次 cron が1回失敗しても次回実行で埋め合わせられるよう、直近何件のABCを
# 重複チェック対象にするか。3件あれば3週分の取りこぼしまでカバーできる。
CONTESTS_TO_CHECK = 3

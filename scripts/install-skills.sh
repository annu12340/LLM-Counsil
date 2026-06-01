#!/usr/bin/env bash
# Install all Agent Skills from skills/ into Cursor or Claude Code discovery paths.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_SRC="${REPO_ROOT}/skills"

TARGET="cursor"       # cursor | claude
SCOPE="personal"        # personal | project
USE_SYMLINK=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: ./scripts/install-skills.sh [options]

Install every skill package under skills/ into the agent skills directory.

Options:
  --target cursor|claude   Agent environment (default: cursor)
  --scope personal|project personal = ~/.cursor or ~/.claude skills
                           project  = .cursor/skills or .claude/skills in this repo
  --symlink                Symlink instead of copy (edits in skills/ apply after new session)
  --dry-run                Print actions without installing
  -h, --help               Show this help

Examples:
  ./scripts/install-skills.sh
  ./scripts/install-skills.sh --target claude --scope personal
  ./scripts/install-skills.sh --scope project
  ./scripts/install-skills.sh --symlink

After install, start a new Agent chat (skills load at session startup).
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:?}"
      shift 2
      ;;
    --scope)
      SCOPE="${2:?}"
      shift 2
      ;;
    --symlink) USE_SYMLINK=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

case "$TARGET" in
  cursor|claude) ;;
  *) echo "Invalid --target: $TARGET (use cursor or claude)" >&2; exit 1 ;;
esac

case "$SCOPE" in
  personal|project) ;;
  *) echo "Invalid --scope: $SCOPE (use personal or project)" >&2; exit 1 ;;
esac

if [[ "$SCOPE" == "personal" ]]; then
  if [[ "$TARGET" == "cursor" ]]; then
    DEST_ROOT="${HOME}/.cursor/skills"
  else
    DEST_ROOT="${HOME}/.claude/skills"
  fi
else
  if [[ "$TARGET" == "cursor" ]]; then
    DEST_ROOT="${REPO_ROOT}/.cursor/skills"
  else
    DEST_ROOT="${REPO_ROOT}/.claude/skills"
  fi
fi

skill_name_from_frontmatter() {
  local skill_md="$1"
  if [[ ! -f "$skill_md" ]]; then
    echo ""
    return 1
  fi
  awk -F': ' '/^name:/ { print $2; exit }' "$skill_md" | tr -d '\r' | sed 's/^["'\'']//;s/["'\'']$//'
}

install_one() {
  local src_dir="$1"
  local folder_name
  folder_name="$(basename "$src_dir")"
  local skill_md="${src_dir}/SKILL.md"
  local dest_name

  if [[ ! -f "$skill_md" ]]; then
    echo "Skipping ${folder_name} (no SKILL.md)" >&2
    return 0
  fi

  dest_name="$(skill_name_from_frontmatter "$skill_md")"
  if [[ -z "$dest_name" ]]; then
    dest_name="$folder_name"
    echo "Warning: no name: in ${skill_md}, using folder name ${dest_name}" >&2
  fi

  local dest_path="${DEST_ROOT}/${dest_name}"

  if [[ $DRY_RUN -eq 1 ]]; then
    if [[ $USE_SYMLINK -eq 1 ]]; then
      echo "[dry-run] ln -sfn ${src_dir} ${dest_path}"
    else
      echo "[dry-run] rm -rf ${dest_path} && cp -R ${src_dir} ${dest_path}"
    fi
    return 0
  fi

  mkdir -p "$DEST_ROOT"
  if [[ -e "$dest_path" || -L "$dest_path" ]]; then
    rm -rf "$dest_path"
  fi

  if [[ $USE_SYMLINK -eq 1 ]]; then
    ln -sfn "$src_dir" "$dest_path"
    echo "Linked ${folder_name} -> ${dest_path}"
  else
    cp -R "$src_dir" "$dest_path"
    echo "Installed ${folder_name} -> ${dest_path}"
  fi
}

if [[ ! -d "$SKILLS_SRC" ]]; then
  echo "No skills/ directory at ${SKILLS_SRC}" >&2
  exit 1
fi

shopt -s nullglob
skill_dirs=("${SKILLS_SRC}"/*/)
if [[ ${#skill_dirs[@]} -eq 0 ]]; then
  echo "No skill packages found in ${SKILLS_SRC}" >&2
  exit 1
fi

echo "Source:      ${SKILLS_SRC}"
echo "Destination: ${DEST_ROOT}"
echo "Mode:        $([[ $USE_SYMLINK -eq 1 ]] && echo symlink || echo copy)"
echo ""

for dir in "${skill_dirs[@]}"; do
  [[ -d "$dir" ]] || continue
  install_one "$dir"
done

echo ""
echo "Done. Start a new ${TARGET} Agent session to load skills."

function add_worktree -d "Create a git worktree and cd into it"
    set -l no_cd false
    set -l branch_name ""

    for arg in $argv
        switch $arg
            case --no-cd
                set no_cd true
            case '*'
                set branch_name $arg
        end
    end

    if test -z "$branch_name"
        echo "Usage: add_worktree <branch-name> [--no-cd]"
        echo "Example: add_worktree carson/main-2330-desktop-changelog"
        echo "Example: add_worktree my-feature"
        return 1
    end

    # Find a git worktree/repo to operate from, and determine where to place new worktrees
    set -l git_dir ""
    set -l wt_root ""

    if git rev-parse --git-dir >/dev/null 2>&1
        # Inside a git repo or worktree
        set git_dir (git rev-parse --show-toplevel)
        set wt_root (dirname $git_dir)
    else
        # Not in a git repo — look for one in subdirectories (e.g. main/)
        set wt_root $PWD
        for subdir in $PWD/main $PWD/*/
            set subdir (string trim --right --chars=/ $subdir)
            if test -d "$subdir"; and git -C $subdir rev-parse --git-dir >/dev/null 2>&1
                set git_dir $subdir
                break
            end
        end
    end

    if test -z "$git_dir"
        echo "Error: no git repository found (try running from inside a repo or a worktree parent)"
        return 1
    end

    # Determine worktree path
    set -l wt_path "$wt_root/$branch_name"

    # Fetch latest from origin
    echo "Fetching from origin..."
    git -C $git_dir fetch origin

    # Check if worktree already exists at this path
    if test -d "$wt_path"
        echo "Worktree already exists at: $wt_path"
        if test "$no_cd" = false
            cd $wt_path
        end
        return 0
    end

    # Check if branch exists locally, on remote, or needs creating
    set -l local_exists (git -C $git_dir branch --list $branch_name 2>/dev/null | string trim)
    set -l remote_exists (git -C $git_dir ls-remote --heads origin $branch_name 2>/dev/null | string match -q "*$branch_name*" && echo yes)

    if test -n "$local_exists"
        echo "Branch '$branch_name' exists locally, creating worktree..."
        git -C $git_dir worktree add $wt_path $branch_name
    else if test "$remote_exists" = yes
        echo "Branch '$branch_name' exists on origin, checking out..."
        git -C $git_dir worktree add $wt_path $branch_name
        if test $status -eq 0
            git -C $wt_path branch --set-upstream-to=origin/$branch_name $branch_name 2>/dev/null
        end
    else
        echo "Branch '$branch_name' not found, creating new branch from origin/main..."
        git -C $git_dir worktree add $wt_path -b $branch_name origin/main
    end

    if test $status -ne 0
        echo "Failed to create worktree"
        return 1
    end

    echo "Worktree created at: $wt_path"

    if test "$no_cd" = false
        cd $wt_path
    end
end

function add_worktree -d "Create a git worktree and cd into it"
    # Find add_worktree.sh by walking up from $PWD
    set -l dir $PWD
    set -l script ""
    while test "$dir" != "/"
        if test -f "$dir/add_worktree.sh"
            set script "$dir/add_worktree.sh"
            break
        end
        set dir (dirname $dir)
    end

    if test -z "$script"
        echo "Error: add_worktree.sh not found in any parent directory"
        return 1
    end

    set -l no_cd false
    set -l args

    for arg in $argv
        if test "$arg" = "--no-cd"
            set no_cd true
        else
            set -a args $arg
        end
    end

    if test (count $args) -eq 0
        echo "Usage: add_worktree <ticket-name> [--no-cd]"
        echo "Example: add_worktree carson/main-2330-desktop-changelog"
        echo "Example: add_worktree MAIN-2494"
        return 1
    end

    set -l output (bash $script $args[1] 2>&1 | tee /dev/stderr | string match 'WORKTREE_PATH:*')

    if test -n "$output"; and test "$no_cd" = false
        set -l wt_path (string replace 'WORKTREE_PATH:' '' $output)
        cd $wt_path
    end
end

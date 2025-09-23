#!/bin/bash

PORT=8001
COMMANDS=()
DEFAULT_COMMANDS=("convert_nbs" "convert_src_nbs" "serve_docs")
RUN_DEFAULTS=true
errors=()

handle_error() {
    local error_msg="$1"
    echo -e "\n❌ Error: $error_msg"
    errors+=("$error_msg")
}

show_usage() {
    echo "Usage: $0 [commands] [options]"
    echo "Commands:"
    echo "  convert_nbs  - Convert tutorials notebooks to markdown"
    echo "  convert_analysis - Convert analysis notebooks to markdown"
    echo "  convert_src_nbs  - Convert all src notebooks to markdown"
    echo "  serve_docs       - Start local documentation server"
    echo ""
    echo "Options:"
    echo "  --port PORT  - Specify port for docs server (default: 8001)"
    echo ""
    exit 1
}

while [ $# -gt 0 ]; do
    case "$1" in
        convert_nbs|convert_analysis|convert_src_nbs|serve_docs)
            COMMANDS+=("$1")
            RUN_DEFAULTS=false
            ;;
        --port)
            PORT="$2"; shift ;;
        --help|-h)
            show_usage ;;
        *)
            echo "Unknown parameter: $1"; show_usage ;;
    esac
    shift
done

if [ $RUN_DEFAULTS = true ]; then
    COMMANDS=("${DEFAULT_COMMANDS[@]}")
fi

convert_notebooks() {
    echo -e "\n🔄 Converting tutorial notebooks to markdown..."
    mkdir -p docs/tutorials
    jupyter nbconvert --to markdown tutorials/*.ipynb --output-dir docs/tutorials/ --TagRemovePreprocessor.remove_cell_tags hide 2>/tmp/nb_error || {
        error_content="Failed to convert notebooks to markdown:\n$(cat /tmp/nb_error)"
        handle_error "$error_content"
    }
}

convert_analysis() {
    echo -e "\n🔄 Converting analysis notebooks to markdown..."
    mkdir -p docs/reference/analysis/notebooks
    jupyter nbconvert --to markdown ../src/epiphyte/analysis/visualization/*.ipynb \
        --output-dir docs/reference/analysis/notebooks/ \
        --TagRemovePreprocessor.remove_cell_tags hide 2>/tmp/nb_error || {
        error_content="Failed to convert analysis notebooks to markdown:\n$(cat /tmp/nb_error)"
        handle_error "$error_content"
    }
}

convert_src_nbs() {
    echo -e "\n🔄 Converting all src notebooks to markdown..."
    base_src="../src"
    out_base="docs/reference/src_nbs"
    mkdir -p "$out_base"
    while IFS= read -r nb; do
        rel="${nb#$base_src/}"
        rel_dir="$(dirname "$rel")"
        target_dir="$out_base/$rel_dir"
        mkdir -p "$target_dir"
        jupyter nbconvert --to markdown "$nb" --output-dir "$target_dir" \
            --TagRemovePreprocessor.remove_cell_tags hide 2>/tmp/nb_error || {
            error_content="Failed to convert $nb to markdown:\n$(cat /tmp/nb_error)"
            handle_error "$error_content"
        }
    done < <(find "$base_src" -type f -name "*.ipynb")
}

serve_docs() {
    echo -e "\n🔄 Starting local docs server on port $PORT..."
    (cd docs && mkdocs serve -a localhost:$PORT)
}

for cmd in "${COMMANDS[@]}"; do
    case $cmd in
        convert_nbs) convert_notebooks ;;
        convert_analysis) convert_analysis ;;
        convert_src_nbs) convert_src_nbs ;;
        serve_docs) serve_docs ;;
    esac
done

echo -e "\n📋 Summary:"
if [ ${#errors[@]} -eq 0 ]; then
    echo "✅ All steps completed successfully!"
else
    echo "⚠️ The following errors occurred during execution:"
    echo "----------------------------------------"
    printf '%s\n\n' "${errors[@]}"
fi

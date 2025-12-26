find src -name '*.py' ! -path './.venv/*' -exec wc -l {} + | sort -n
